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
import{loggingApi as t}from"../common/loggingApi.js";import e from"./CacheStore.js";import{floodgate as o}from"./floodgate.js";import{dcLocalStorage as r}from"../common/local-storage.js";const i=new class{constructor(){this.THIRTY_DAYS=2592e6,this.promise=null}safeJsonParse(t){try{return JSON.parse(t)}catch(t){return null}}async fetch(t){const e=await fetch(t);if(!e.ok)throw new Error(`Failed to fetch block list from ${t}: ${e.statusText}`);return(await e.text()).split("\n").map((t=>t.trim())).filter((t=>t.length>0))}async _get(){await r.init();const i=await o.hasFlag("dc-cv-domain-moderation-enabled"),s="true"===r.getItem("enableGenAIFab");if(!i||!s)return[];let a=[];const n=new e("explicit-blocklist");try{const t=o.getFeatureMeta("dc-cv-domain-moderation-enabled"),{days:e}=this.safeJsonParse(t)||{},r=e?24*e*60*60*1e3:this.THIRTY_DAYS;if(a=await n.getWithTTL("explicitBlockList"),a&&a.length>0)return a;a=await this.fetch("https://acrobat.adobe.com/dc-hosted-extension/blocked-domains.txt"),a&&a.length>0&&await n.setWithTTL("explicitBlockList",a,r)}catch(e){t.error({message:"Error fetching explicit block list from Adobe",error:e.toString()})}return a||[]}get(){return this.promise||(this.promise=this._get()),this.promise}};export default i;