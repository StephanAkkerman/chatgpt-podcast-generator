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
import{sendAnalytics}from"../gsuite/util.js";let abortController=new AbortController,internalState={lruThreadsData:new Map};const state={gmailConfig:{},expressConfig:{},getMessagesForThreadId(e){let t=internalState.lruThreadsData.get(e);return t?(internalState.lruThreadsData.delete(e),internalState.lruThreadsData.set(e,t),t.messages):null},updateLRUThreadData(e){const t=this.gmailConfig?.selectors?.listView?.maxLRUSizeForThreadData||3e3,r=internalState.lruThreadsData;if(r.has(e.id))r.delete(e.id);else if(r.size===t){const e=r.keys().next().value;r.delete(e),sendAnalytics([["DCBrowserExt:Gmail:ResponseLRU:Full"]])}r.set(e.id,e)},setDataForThread(e){this.updateLRUThreadData(e)},get eventControllerSignal(){return abortController.signal},nativeViewerPromptState:{nativeViewerPromptVisible:!1,previousFileDetailsElement:null,nativeViewerAttachmentURL:null,driveButtonAddedListeners:{}},expressState:{nativeViewerTouchpointVisible:!1,imageURL:null},iconURL:"",iconURLListView:"",viewerURLPrefix:"",disconnectExpressObserver:!1,disconnectAcrobatObserver:!1,get disconnectBodyObserver(){return this.disconnectExpressObserver&&this.disconnectAcrobatObserver},adobeCleanFontAdded:!1,gmailResponseListenerAdded:!1,disconnectEventListeners(){this.disconnectExpressListeners(),this.disconnectAcrobatListeners()},disconnectExpressListeners(){this.disconnectExpressObserver=!0},disconnectAcrobatListeners(){abortController.abort(),this.disconnectAcrobatObserver=!0},resetDOMElementListener(){abortController?.abort(),abortController=new AbortController},createStateToTransferToNewContentScript:()=>({internalState:internalState,gmailResponseListenerAdded:state?.gmailResponseListenerAdded,adobeCleanFontAdded:state?.adobeCleanFontAdded,isAcrobatDefaultForGmailPDFs:state?.isAcrobatDefaultForGmailPDFs}),contentScriptDisconnectStart(){chrome.runtime?.id||(this.disconnectEventListeners(),this.nativeViewerPromptState={})},contentScriptDisconnectEnd(e){if(!chrome.runtime?.id)return;const t=e?.detail?.state;internalState=t?.internalState,this.gmailResponseListenerAdded=t?.gmailResponseListenerAdded,this.adobeCleanFontAdded=t?.adobeCleanFontAdded,this.isAcrobatDefaultForGmailPDFs=t?.isAcrobatDefaultForGmailPDFs},fteToolTip:{},isAcrobatDefaultForGmailPDFs:!1,analyticsForImageInAPIResponse:!1,analyticsForImageClicked:!1};export default state;