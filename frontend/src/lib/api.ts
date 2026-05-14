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
	let finished = false;  // ← track if we're done

	es.onmessage = (e) => {
		const outer = JSON.parse(e.data);
    const data = outer.data ?? outer;
		const status: string = data.status;
		onStatus(status);
		if (status === 'done') {
			finished = true;
			es.close();
			onDone();
		} else if (status.startsWith('error')) {
			finished = true;
			es.close();
			onError(status);
		}
	};

	es.onerror = () => {
		es.close();
		if (!finished) onError('Connection lost');  // ← only error if not already done
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
	const params = new URLSearchParams({ repo_url: repoUrl, question, session_id: sessionId });
	const es = new EventSource(`${BASE_URL}/chat?${params.toString()}`);
	let finished = false;
	let lastToken = '';

	es.onmessage = (e) => {
		const outer = JSON.parse(e.data);
		const token: string = outer.data ?? outer;
		// backend sends each token, then repeats the full response as final event
		// we buffer one token behind so we can drop the last (full) one
		if (lastToken) onToken(lastToken);
		lastToken = token;
	};

	es.onerror = () => {
		es.close();
		if (!finished) {
			finished = true;
			onDone();
		}
	};

	return () => { finished = true; es.close(); };
}
