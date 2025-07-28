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
import{dcLocalStorage as o}from"../../../common/local-storage.js";import{events as t}from"../../../common/analytics.js";import{LOCAL_FILE_PERMISSION_URL as e,ONE_DAY_IN_MS as n}from"../../../common/constant.js";import{floodgate as r}from"../../../sw_modules/floodgate.js";import{util as i}from"../../js/content-util.js";import{loggingApi as a}from"../../../common/loggingApi.js";const l="Error in Local File Prompt";async function s(){try{i.translateElements(".translate");const t=document.getElementById("local-file-animated-fte");t?t.style.backgroundImage="url(../../images/LocalizedFte/en_US/fte_old.svg)":a.error({message:l+"initialize: FTE element not found"});document.getElementById("localFilePromptContinueButton").addEventListener("click",c),await o.init()}catch(o){a.error({message:l,error:`initialize: Error in initialization: ${o}`})}}async function c(){try{i.sendAnalytics(t.LOCAL_FTE_GO_TO_SETTINGS_CLICKED);!function(t){try{let e=o.getItem("localFileConfig");e||(e={promptCount:1}),e.eligibleDate=function(o){const t=Number(o?.settingsCoolDown);Number.isNaN(t)&&a.error({message:l,error:`_getLocalFilePromptCooldown: cooldownConfig.settingsCoolDown must be a valid number: ${o?.settingsCoolDown}`});return new Date(Date.now()+t*n).toISOString()}(t),o.setItem("localFileConfig",e)}catch(o){a.error({message:l,error:`_updateLocalFilePromptCooldown: Error updating local file prompt cooldown: ${o}`})}}(await function(){let o;try{o=r.getFeatureMeta("dc-cv-local-file-permission-prompt"),o=JSON.parse(o)}catch(t){o={promptLimit:5,ignoreCoolDown:7,settingsCoolDown:7,dismissCoolDown:7}}return o}());const s=o.getItem("localFteWindow");if(s){const{id:t,height:n,width:r,left:i,top:c}=s;chrome.windows.create({height:n,width:r,left:i,top:c,focused:!0,type:"popup",url:e},(e=>{chrome.runtime.lastError?a.error({message:l,error:"handleSettingsButtonCLick: Error creating window"}):(o.setItem("settingsWindow",{id:e.tabs[0].id}),chrome.windows.remove(t))}))}else a.error({message:l,error:"handleSettingsButtonCLick: Window configuration not found in storage"})}catch(o){a.error({message:l,error:`handleSettingsButtonCLick: Error in button click handler: ${o}`})}}"loading"===document.readyState?document.addEventListener("DOMContentLoaded",s):s();