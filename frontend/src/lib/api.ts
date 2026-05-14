const BASE_URL = 'http://localhost:8000';

export async function ingestRepo(repoUrl: string): Promise<string> {
	const res = await fetch(`${BASE_URL}/ingest?repo_url=${encodeURIComponent(repoUrl)}`, {
		method: 'POST'
	});
	if (!res.ok) throw new Error('Failed to start ingestion');
	const data = await res.json();
	return data.task_id;
}

export function watchIngestStatus(
	taskId: string,
	onStatus: (status: string) => void,
	onDone: () => void,
	onError: (err: string) => void
): () => void {
	const es = new EventSource(`${BASE_URL}/status?task_id=${taskId}`);

	es.onmessage = (e) => {
		const data = JSON.parse(e.data);
		const status: string = data.status;
		onStatus(status);
		if (status === 'done') {
			es.close();
			onDone();
		} else if (status.startsWith('error')) {
			es.close();
			onError(status);
		}
	};

	es.onerror = () => {
		es.close();
		onError('Connection lost');
	};

	return () => es.close();
}

export function streamChat(
	repoUrl: string,
	question: string,
	sessionId: string,
	onToken: (token: string) => void,
	onDone: () => void,
	onError: (err: string) => void
): () => void {
	const params = new URLSearchParams({
		repo_url: repoUrl,
		question,
		session_id: sessionId
	});

	const es = new EventSource(`${BASE_URL}/chat?${params.toString()}`);
	let lastData = '';

	es.onmessage = (e) => {
		const token = e.data;
		// The last event is the full response; only stream tokens before it
		if (lastData) onToken(lastData);
		lastData = token;
	};

	es.onerror = () => {
		es.close();
		onDone(); // SSE closes after stream ends
	};

	// EventSource doesn't have an explicit "end" event; closing fires onerror
	return () => es.close();
}
