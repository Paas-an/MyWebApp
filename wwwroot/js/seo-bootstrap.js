// The published HTML includes route metadata for crawlers without JavaScript.
// Hand ownership to Blazor's HeadOutlet before startup so client navigation
// replaces metadata instead of leaving duplicate canonical/description tags.
document.querySelectorAll("[data-initial-seo]").forEach(element => element.remove());
