interface MessageTypes{
    turn_rank:Array<number>,
    current_query:string,
    context:Array<Array<string>>,
    prev_queries:Array<string>,
    prev_responses:Array<string>,
    confidence_score:Array<number>,
    category:Array<number>,
}

interface actionTypes{
    type:string,
    payload:{
        current_query:string,
        reason:string, 
        confidence_score:number,
        response:string,
        category:number,
        context:Array<string>
    }
}


let initialState:MessageTypes={turn_rank:[1],prev_queries:[],prev_responses:[],current_query:'',confidence_score:[],category:[],context:[]}

const ChatMessagesReducer=(state:MessageTypes=initialState,action:actionTypes)=>{
    let data=null
    switch(action.type){
        // turn_rank=1 current_query='asdasdasdasdsa' prev_queries=[] prev_responses=[]
        case 'update new response':
            data=action.payload
            
            state={...state,
                    turn_rank:[...state.turn_rank, state.turn_rank[state.turn_rank.length-1]+1],
                    prev_queries:[...state.prev_queries, data.current_query], 
                    prev_responses:[...state.prev_responses, data.response],
                    confidence_score:[...state.confidence_score, data.confidence_score],
                    current_query:'',
                    category:[...state.category,data.category],
                    context:[...state.context,action.payload.context]
                    
                }
            return state

        default:
            return state;
    }
}

export default ChatMessagesReducer