import { combineReducers, createStore } from "redux";
import { applyMiddleware } from "redux";
import { thunk } from "redux-thunk";

import ChatMessagesReducer from "./reducers/ChatMessagesReducer";
import ChatDisplayReducer from "./reducers/ChatDisplay";
import NavigationReducer from "./reducers/NavigationReducer";

const combineReducer=combineReducers({ChatMessagesReducer, ChatDisplayReducer, NavigationReducer})

const store = createStore(combineReducer,{},applyMiddleware(thunk))

export default store