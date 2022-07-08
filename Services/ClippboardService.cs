using System.Threading.Tasks;
using Microsoft.JSInterop;
namespace webapp.Services
{
    public class ClippboardService
    {
        private readonly IJSRuntime _jsRuntime;

        public ClippboardService(IJSRuntime jsRuntime)
        {
            _jsRuntime = jsRuntime;
        }

        public ValueTask WriteTextAsync(string text)
        {
            return _jsRuntime.InvokeVoidAsync("navigator.clipboard.writeText", text);
        }
    }
}

