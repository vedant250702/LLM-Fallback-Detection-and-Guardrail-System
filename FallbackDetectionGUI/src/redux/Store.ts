import { combineReducers, createStore } from "redux";
import { applyMiddleware } from "redux";
import { thunk } from "redux-thunk";

import ChatMessagesReducer from "./reducers/ChatMessagesReducer";
import ChatDisplayReducer from "./reducers/ChatDisplay";
import NavigationReducer from "./reducers/NavigationReducer";
import AnalysisReducer from "./reducers/AnalysisReducer";

const combineReducer=combineReducers({ChatMessagesReducer, ChatDisplayReducer, NavigationReducer, AnalysisReducer})

const store = createStore(combineReducer,{},applyMiddleware(thunk))

export default store