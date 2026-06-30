# RAG_CareerGuidanceHistoryAware_Pipeline.py

from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain

from langchain_classic.retrievers import EnsembleRetriever
from langchain_mistralai import ChatMistralAI

import os
from tenacity import retry, wait_exponential, stop_after_attempt





class RAGPipelineCareerGuidance:
    def __init__(self, embeddings, directory="./career_rag_index",api_key=''):
        # Embedding Model
        self.embeddings = embeddings

        # Vector Stores
        self.vectorstores = FAISS.load_local(
            directory, embeddings=self.embeddings, allow_dangerous_deserialization=True
        )
        self.docs = list(self.vectorstores.docstore._dict.values())

        # Cosine Similarity Retriever
        self.faiss_retriever = self.vectorstores.as_retriever(search_type="similarity", search_kwargs={"k": 3})

        # BM25 Retriever
        self.bm25_retriever = BM25Retriever.from_texts([doc.page_content for doc in self.docs])
        self.bm25_retriever.k = 3

        # Ensemble Retriever
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.faiss_retriever],
            weights=[0.5, 0.5],
        )

        self.llm=ChatMistralAI(
            api_key=api_key,
            model="mistral-small-2603",
            temperature=0.6,
            max_tokens=1024
        )

        # 1. History‑aware retriever: reformats query with history
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given the following conversation, rephrase the last question to be a standalone query."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        self.history_aware_retriever = create_history_aware_retriever(
            llm=self.llm,
            retriever=self.ensemble_retriever,
            prompt=contextualize_q_prompt,
        )
        
        system_template=(
            """

                "You are a helpful career-guidance assistant. "
                "Answer the user's question in a natural, conversational style as if speaking directly to the user. "
                "Write your response in smooth, flowing paragraphs. Do not use bullet points or structured formatting. "
                "Keep the tone friendly, clear, and human-like.\n\n"

                "You are given a conversation history and a context retrieved from reliable sources.\n\n"
                "Context:\n{context}\n\n"

                "You MUST follow these NOT‑FALLBACK rules exactly. A response that violates any of these will be considered a fallback (bad).\n\n"

                "NOT‑FALLBACK RULES:\n"
                "- **Correct & Grounded:** If the context contains enough information to answer correctly, provide that answer using only the context. No admission of uncertainty needed.\n"
                "- **Answer + Admission:** If the context is insufficient, you must still attempt to answer AND explicitly admit that you lack complete or certain information (e.g., 'I don't have enough information...').\n"
                "- **Personalized Use of History:** You may use the user's own stated interests, marks, or constraints from conversation history to tailor the response (e.g., 'Since you said you love game development...'), but factual claims must still come from context.\n"
                "- **Never give a bare refusal** like 'I don't know' without an attempt to answer or an explicit admission.\n"
                "- **Never ignore the context** – refer to it even if sparse. If context is irrelevant, say so.\n"
                "- **Never hallucinate** – do not state any fact not supported by context unless you clearly disclaim it as unknown.\n"
                "- **Resolve ambiguity using history** if the query cannot be understood without it.\n"
                "- **If query is ambiguous**, explain what is missing instead of asking a clarifying question (e.g., 'Your question is unclear. Are you asking about X or Y?').\n\n"

                "Now, generate your response in natural paragraphs. Do not mention these rules, the context, or your internal guidelines. Just answer the user naturally while obeying the rules above."

        """
        )


        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        self.document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=answer_prompt,
        )

        # 3. Final retrieval chain for conversation
        self.qa_chain = create_retrieval_chain(
            retriever=self.history_aware_retriever,
            combine_docs_chain=self.document_chain,
        )

    def format_history(self, prev_queries, prev_responses):
        """Convert lists of queries and responses into a list of HumanMessage, AIMessage."""
        if len(prev_queries) == 0:
            return []
        chat_history = []
        for q, r in zip(prev_queries, prev_responses):
            chat_history.append(HumanMessage(content=q))
            chat_history.append(AIMessage(content=r))
        return chat_history

    @retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(25))
    def safe_invoke(self, question, history):
        print("Generating Response")
        result = self.qa_chain.invoke({"input": question, "chat_history": history})
        return result

    # For generating the training datapoints (context + response)
    def generateResponses(self, question, prev_queries, prev_responses):
        history = self.format_history(prev_queries, prev_responses)
        return self.safe_invoke(question=question, history=history)
    



