// This Reducer is specfically used for Handling the navigations.
interface actionTypes{
    type:string,
    payload:boolean | null
}

interface NavigationTypes{
    analysis_panel:boolean,
    dashboard_panel:boolean,
    analysis_loading:boolean | null
}


let initialState:NavigationTypes={analysis_panel:false,dashboard_panel:false, analysis_loading:false}

const NavigationReducer=(state:NavigationTypes=initialState,action:actionTypes)=>{
    switch(action.type){
        case 'toggle analysis panel':
            if (action.payload!=null){
                state={...state,analysis_panel:action.payload}
            }else{
                state={...state,analysis_panel:!state.analysis_panel}
            }

            return state
        
        case 'toggle drawer panel':
            state={...state,dashboard_panel:!state.dashboard_panel}
            return state

        case 'toggle analysis loading':
            state={...state,analysis_loading:action.payload}
            return state


        default:
            return state;
    }
}

export default NavigationReducer