const { BrowserManager } = require('agent-browser');

async function start() {
    const browser = new BrowserManager();
    // Setting the port via the internal API is more reliable than environment variables
    process.env.AGENT_BROWSER_STREAM_PORT = '9223'; 
    
    await browser.launch({ headless: false });
    await browser.navigate('https://google.com');
    
    console.log("Streaming server is LIVE on ws://localhost:9223");
    console.log("Press Ctrl+C to stop.");
    
    // This keeps the Node process alive indefinitely
    setInterval(() => {}, 1000); 
}

start();