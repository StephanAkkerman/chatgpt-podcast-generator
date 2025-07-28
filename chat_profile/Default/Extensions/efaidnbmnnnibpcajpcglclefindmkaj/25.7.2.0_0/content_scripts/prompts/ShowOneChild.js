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
const actionableCoachmark=new ActionableCoachmark,gmailAcrobatFteCoachmark=new GmailAcrobatFteCoachmark,embeddedPDFTouchPointCoachMark=new EmbeddedPDFTouchPointCoachMark,whatsappExpressFte=new WhatsappExpressFte,outlookFte=new OutlookFte,gmailExpressFte=new GmailExpressFte;class ShowOneChild{constructor(){this.expressFte=this.getExpressFte(),this.prompts=[actionableCoachmark,{id:"ExpressFte",isEligible:async()=>(await this.expressFte).isExpressFteEligible(),render:async()=>{(await this.expressFte).renderExpressFte()},timeout:3e3},embeddedPDFTouchPointCoachMark,outlookFte,whatsappExpressFte,gmailAcrobatFteCoachmark,gmailExpressFte],this.subscribeToPromptEvents(),window.addEventListener("beforeunload",this.releaseLock)}async getExpressFte(){const e=chrome.runtime.getURL("content_scripts/express/express-fte.js");return(await import(e)).default}subscribeToPromptEvents=()=>{chrome.runtime.onMessage.addListener((async e=>{switch(e.action){case"clearRenderPrompt":await initDcLocalStorage(),window.dcLocalStorage?.removeItem("renderPrompt");break;case"reRenderShowOneChild":this.render()}}))};setRenderPromptTTL(e){window.dcLocalStorage?.setWithTTL("renderPrompt",e?.id,864e5)}lockRenderPrompt(){window.dcLocalStorage?.setWithTTL("renderPrompt","locked",2e3)}releaseLock(){const e=window.dcLocalStorage?.getWithTTL("renderPrompt");"locked"===e&&(window.dcLocalStorage?.removeItem("renderPrompt"),chrome.runtime.sendMessage({main_op:"local-storage-remove",key:"renderPrompt"}))}readRenderPromptFromStorage=async()=>{let e=0,t=window.dcLocalStorage?.getWithTTL("renderPrompt");for(;"locked"===t;){if(e>=10)return;await new Promise((t=>setTimeout(t,200*(e+1)))),e++,t=window.dcLocalStorage?.getWithTTL("renderPrompt")}return t};getRenderPrompt=async()=>{const e=await this.readRenderPromptFromStorage();if(""===e||!this.prompts.some((t=>t.id===e)))try{this.lockRenderPrompt();for(const e of this.prompts)e.eligiblityPromise=e?.isEligible?.();for(const e of this.prompts){if(await PromiseTimeout(e.eligiblityPromise,{timeout:e?.timeout??2e3}))return this.setRenderPromptTTL(e),e}return}finally{this.releaseLock()}};getRenderedPromptId=()=>this.renderedPromptId;render=async()=>{const e=await this.getRenderPrompt();return e&&e.render&&e.render(),this.renderedPromptId=e?.id,e?.id}}const showOneChild=new ShowOneChild;