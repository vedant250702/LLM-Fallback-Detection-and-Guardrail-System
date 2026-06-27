// This Reducer is specfically used for storing the React Functional Components in the Array.

interface actionTypes{
    type:string,
    payload:{
        role:string,
        message:string
    }
}

interface MessageTypes{
    messages:Array<{role:string,message:string}>
}


let initialState:MessageTypes={messages:[]}

const ChatDisplayReducer=(state:MessageTypes=initialState,action:actionTypes)=>{
    let data=null
    switch(action.type){
        case 'add chat component':
            data=action.payload
            state={...state,messages:[...state.messages,data]}
            return state

        default:
            return state;
    }
}

export default ChatDisplayReducer