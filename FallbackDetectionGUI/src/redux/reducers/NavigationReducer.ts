// This Reducer is specfically used for Handling the navigations.

import React, { act } from "react"



interface actionTypes{
    type:string,
    payload:boolean
}

interface NavigationTypes{
    analysis_panel:boolean,
    dashboard_panel:boolean
}


let initialState:NavigationTypes={analysis_panel:false,dashboard_panel:false}

const NavigationReducer=(state:NavigationTypes=initialState,action:actionTypes)=>{
    switch(action.type){
        case 'toggle analysis panel':
            state={...state,analysis_panel:!state.analysis_panel}
            return state
        
        case 'toggle drawer panel':
            state={...state,dashboard_panel:!state.dashboard_panel}
            return state
        default:
            return state;
    }
}

export default NavigationReducer