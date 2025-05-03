const SERVER_URL = 'http://127.0.0.1:8000/stream';

async function connectAndReadStream() {
    const response = await fetch(SERVER_URL);

    if (!response.body) {
        console.error("No response body.");
        return;
    }

    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('text/event-stream')) {
        console.error(`Expected text/event-stream, got ${contentType}`);
        console.error(await response.text());
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const eventString of events) {
            if (!eventString.trim()) continue;
            let eventType = 'message', eventData = '';
            for (const line of eventString.split('\n')) {
                if (line.startsWith(':')) continue;
                if (line.startsWith('event: ')) eventType = line.slice(7).trim();
                else if (line.startsWith('data: ')) eventData += (eventData ? '\n' : '') + line.slice(6);
            }
            switch (eventType) {
                case 'status':
                    console.log(`STATUS: ${eventData}`);
                    break;
                case 'retrieved_sources':
                    console.log(`RETRIEVED SOURCES: ${eventData}`);
                    break;
                case 'token':
                    process.stdout.write(eventData);
                    break;
                case 'citation':
                    console.log(`\nCITATION: ${eventData}`);
                    break;
                case 'end':
                    console.log(`\nEND: ${eventData}`);
                    return;
                default:
                    console.log(`${eventType.toUpperCase()}: ${eventData}`);
            }
        }
    }
}

connectAndReadStream();