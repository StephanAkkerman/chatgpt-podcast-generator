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
class ExpressFteUtils{addFontToDocument=async()=>{if("true"===sessionStorage.getItem("adobeCleanFontAdded"))return;const e=chrome.runtime.getURL("browser/css/fonts/AdobeClean-Regular.otf"),t=chrome.runtime.getURL("browser/css/fonts/AdobeClean-Bold.otf"),o=new FontFace("AdobeClean-Regular",`url(${e})`),s=new FontFace("AdobeClean-Bold",`url(${t})`);document.fonts.add(o),document.fonts.add(s),await o.load(),await s.load(),sessionStorage.setItem("adobeCleanFontAdded","true")};isExpressFteTooltipSecond=async()=>{const{env:e}=await chrome.storage.local.get("env");if("prod"===e)return!1;return!!new URLSearchParams(window.location.search).has("expressFteTooltipSecond")};sendAnalyticsEvent=e=>{try{chrome.runtime.sendMessage({main_op:"analytics",analytics:e})}catch(e){}}}const expressFteUtils=new ExpressFteUtils;export default expressFteUtils;