/* GTM bootstrap — externalized for strict CSP (script-src 'self'). Card #97.
   Loads the container LOADER first-party from sgtm.swarph.ai (nginx path-split ->
   googletagmanager). Consent Mode default (denied) is already set by
   consent-default.js, which runs BEFORE this file in <head>. */
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});
var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';
j.async=true;j.src='https://sgtm.swarph.ai/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-N9VZ27G3');
