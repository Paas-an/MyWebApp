// Let Blazor's HeadOutlet replace the initial route metadata without duplicates.
document.querySelectorAll("[data-initial-seo]").forEach(element => element.remove());
