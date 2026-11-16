<#import "template.ftl" as layout>
<#assign showBanner = message?? && message?has_content && message.type != "warning">
<@layout.registrationLayout displayInfo=true displayMessage=showBanner; section>
    <#if section = "header">
        ${msg("emailVerifyTitle")}
    <#elseif section = "form">
        <#assign sentTo = (user.email)!"">
        <#assign instruction = msg("emailVerifyInstruction1", sentTo)>
        <div class="vigia-verify">
            <div class="vigia-verify__mark" aria-hidden="true"></div>
            <#if message?? && message?has_content && message.type == "warning">
                <p class="vigia-verify__title">${kcSanitize(message.summary)?no_esc}</p>
            </#if>
            <p class="vigia-verify__text">
                <#if sentTo?has_content && instruction?contains(sentTo)>
                    <#list instruction?split(sentTo) as part>${part}<#if part?has_next><strong class="vigia-verify__email">${sentTo}</strong></#if></#list>
                <#else>
                    ${instruction}
                </#if>
            </p>
            <#if sentTo?has_content && !instruction?contains(sentTo)>
                <p class="vigia-verify__address">${sentTo}</p>
            </#if>
        </div>
    <#elseif section = "info">
        <p class="vigia-verify__resend">
            ${msg("emailVerifyInstruction2")}
            <br/>
            <a href="${url.loginAction}">${msg("doClickHere")}</a> ${msg("emailVerifyInstruction3")}
        </p>
    </#if>
</@layout.registrationLayout>
