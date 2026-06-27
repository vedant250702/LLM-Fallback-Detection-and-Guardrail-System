// This Reducer is specfically used for storing the Analysis Information for the specific turn.

interface AnalysisItems{
    reason:string,
    confidence_score:number
}
interface AnalysisTypes{
    collection:{[key:string]:AnalysisItems},
    analysis_turn_rank_number:string | null
}

interface actionTypes{
    type:string,
    payload:{
        reason:string,
        turn_rank:string,
        confidence_score:number
    }
}

let initialState:AnalysisTypes={collection:{}, analysis_turn_rank_number:null}

const AnalysisReducer=(state:AnalysisTypes=initialState,action:actionTypes)=>{

    switch(action.type){
        case 'add analysis information':
            state={...state,collection:{...state.collection,[String(action.payload.turn_rank)]:{reason:action.payload.reason,confidence_score:action.payload.confidence_score}}}
            return state
        case 'current turn_rank':
            console.log(state)
            state={...state,analysis_turn_rank_number:String(action.payload)}
            return state
        default:
            return state;
    }
}

export default AnalysisReducer