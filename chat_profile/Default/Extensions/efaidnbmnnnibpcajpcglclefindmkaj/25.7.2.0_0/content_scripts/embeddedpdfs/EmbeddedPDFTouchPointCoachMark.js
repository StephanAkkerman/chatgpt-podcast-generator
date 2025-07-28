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
const FTE_STATE_STORAGE_KEY="embeddedPDFTouchPointFTEState";let touchPointAddedPromiseResolve,touchPointAddedPromise=new Promise((e=>{touchPointAddedPromiseResolve=e}));class EmbeddedPDFTouchPointCoachMark{shouldResetFteToolTip(e,t){return-1!==e?.resetDay&&t>e?.resetDay}async initFteStateAndConfig(e){const t=(new Date).getTime();let o={count:0,nextDate:t};o=(await chrome.storage.local.get(FTE_STATE_STORAGE_KEY))?.[FTE_STATE_STORAGE_KEY]||o;const i=e?.touchPointConfig?.tooltip;return this?.shouldResetFteToolTip(i,t)&&(o.count=0,o.nextDate=t),chrome.storage.local.set({[FTE_STATE_STORAGE_KEY]:o}),o}constructor(){import(chrome.runtime.getURL("content_scripts/gsuite/fte-utils.js")).then((e=>this.fteUtils=e))}id="embeddedpdfscoachmark";timeout=5e3;async render(){const e=await chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-config"});e?.enableEmbeddedPDFTouchPoint&&chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-fte",frameId:this.frameId})}isTouchPointPresent(){return touchPointAddedPromise}isTouchPointPositionAllowsForFTE(e){return e?.top>=0&&e?.left>=0&&e?.bottom+50<=window.innerHeight&&e?.right<=window.innerWidth}async isEligible(){let e;const t=await chrome.runtime.sendMessage({main_op:"embedded-pdf-touch-point-config"});if(!t?.enableEmbeddedPDFTouchPoint)return Promise.resolve(!1);let o=new Promise((t=>{e=t}));const i=await this.initFteStateAndConfig(t),{isTouchPointPresent:n,frameId:s,position:d}=await this.isTouchPointPresent();if(this.frameId=s,n&&this.isTouchPointPositionAllowsForFTE(d)){const o=t?.touchPointConfig?.tooltip,n=await(this.fteUtils?.shouldShowFteTooltip(o,i,!!o));e(n)}return o}}chrome.runtime.onMessage.addListener((e=>{"added-embedded-pdf-touch-point"===e?.type&&touchPointAddedPromiseResolve({isTouchPointPresent:!0,frameId:e.frameId,position:e.position})}));