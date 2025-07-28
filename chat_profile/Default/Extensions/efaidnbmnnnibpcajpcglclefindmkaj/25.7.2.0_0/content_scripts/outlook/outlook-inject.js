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
!function(){const t=window.fetch;window.fetch=function(...e){const o=e[0]||"";return o&&o.includes("service.svc?action=GetAttachmentDownloadToken")?t(...e).then((t=>(t.ok?(async()=>{const e=t.clone(),o=await e.json();if(e.url)try{const t=new URL(e.url);!t||"outlook.live.com"!==t?.hostname&&"outlook.office.com"!==t?.hostname&&"outlook.office365.com"!==t?.hostname||document.dispatchEvent(new CustomEvent("acrobat-outlook-token-intercept-response",{detail:{success:!0,data:o}}))}catch(t){document.dispatchEvent(new CustomEvent("acrobat-outlook-token-intercept-response",{detail:{success:!1,error:t.message}}))}})():(async()=>{document.dispatchEvent(new CustomEvent("acrobat-outlook-token-intercept-response",{detail:{success:!1,status:t.status}}))})(),t))).catch((t=>{throw document.dispatchEvent(new CustomEvent("acrobat-outlook-token-intercept-response",{detail:{success:!1,error:t.message}})),t})):t(...e)}}();