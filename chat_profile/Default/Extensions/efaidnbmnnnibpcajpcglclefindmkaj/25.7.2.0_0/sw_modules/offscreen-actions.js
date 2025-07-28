/*************************************************************************
* ADOBE CONFIDENTIAL
* ___________________
*
*  Copyright 2015 Adobe Systems Incorporated
*  All Rights Reserved.
*
* NOTICE:  All information contained herein is, and remains
* the property of Adobe Systems Incorporated and its suppliers,
* if any.  The intellectual and technical concepts contained
* herein are proprietary to Adobe Systems Incorporated and its
* suppliers and are protected by all applicable intellectual property laws,
* including trade secret and or copyright laws.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Adobe Systems Incorporated.
**************************************************************************/
import{OFFSCREEN_DOCUMENT_PATH as e}from"../common/constant.js";import{dcLocalStorage as n}from"../common/local-storage.js";import{common as o}from"./common.js";import{communicate as t}from"./communicate.js";import{Proxy as r}from"./proxy.js";import{util as s}from"./util.js";let i=null;i||(i=new function(){this.proxy=r.proxy.bind(this),this.getDocState=function(e){const o=n.getItem("filesData")||{};if(o.filePath)try{const n=new Map(JSON.parse(o.filePath));if(!n.has(e))return;return n.get(e)}catch(e){}},this.setupWorkerOffscreen=async function(t){if(n.getItem("rrv")){const r=o.getEnv(),i=`${e}?env=${r}&rrv=true`;await s.setupOffscreenDocument({path:i,reasons:[chrome.offscreen.Reason.IFRAME_SCRIPTING],justification:"Load iframe in offscreen document"});const a=await chrome.runtime.sendMessage({main_op:"createIframeToLoadAjsWorker",target:"offscreen",rrvEnabled:!0,env:r}),c=n.getItem("lrrv");if(a.iframeLoaded&&c&&t&&!t.startup&&t.acceptRanges&&t.pdfSize>0){const e=this.getDocState(t.pdfURL)||{};chrome.runtime.sendMessage({main_op:"getLinearizedRendition",target:"offscreen",tabId:t.tabId,pdfURL:decodeURIComponent(t.pdfURL),pdfSize:t.pdfSize,docLastOpenState:e})}}},this.closeOffscreenDocument=function(){chrome.offscreen.closeDocument()},this.rapidRenditionResponse=function(e){delete e.main_op,e.content_op="rapidRenditionResponse",chrome.tabs.sendMessage(e.tabId,e)},this.rapidRenditionError=function(e){delete e.main_op,e.content_op="rapidRenditionError",chrome.tabs.sendMessage(e.tabId,e)},this.handleFgResponseFromCDN=async function(t){const r=t.response,i=JSON.parse(r);i.timestamp=Date.now(),n.setItem("ffResponse_anon",JSON.stringify(i));const a=o.getEnv(),c=`${e}?env=${a}`;await s.setupOffscreenDocument({path:c,reasons:[chrome.offscreen.Reason.IFRAME_SCRIPTING],justification:"Load iframe in offscreen document"}),setTimeout((()=>{chrome.runtime.sendMessage({main_op:"fgResponseFromCDN",target:"offscreen",response:JSON.stringify(i),iframeURL:o.getSignInUrl()})}),50)}}),t.registerHandlers({setupWorkerOffscreen:i.proxy(i.setupWorkerOffscreen),closeOffscreenDocument:i.proxy(i.closeOffscreenDocument),rapidRenditionResponse:i.proxy(i.rapidRenditionResponse),rapidRenditionError:i.proxy(i.rapidRenditionError),fgResponseFromCDN:i.proxy(i.handleFgResponseFromCDN)});export const offscreenActions=i;