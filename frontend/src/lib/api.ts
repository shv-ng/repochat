import { PUBLIC_BASE_URL } from '$env/static/public';

const BASE_URL = PUBLIC_BASE_URL;

export async function ingestRepo(repoUrl: string): Promise<string> {
	const res = await fetch(`${BASE_URL}/api/ingest/`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ repo_url: repoUrl })
	});
	if (!res.ok) throw new Error('Failed to start ingestion');
	const data = await res.json();
	return data.job_id;
}

export function watchIngestStatus(
	jobId: string,
	onStatus: (status: string) => void,
	onDone: () => void,
	onError: (err: string) => void
): () => void {
	const es = new EventSource(`${BASE_URL}/api/ingest/?job_id=${jobId}`);
	let finished = false;

	es.onmessage = (e) => {
		const data = JSON.parse(e.data);
		const status: string = data.status;
		onStatus(data.message ?? status);

		if (status === 'completed') {
			finished = true;
			es.close();
			onDone();
		} else if (status === 'error') {
			finished = true;
			es.close();
			onError(data.message ?? 'Ingestion failed');
		}
	};

	es.onerror = () => {
		es.close();
		if (!finished) onError('Connection lost');
	};

	return () => es.close();
}

export function streamChat(
	repoUrl: string,
	query: string,
	sessionId: string,
	onToken: (token: string) => void,
	onDone: () => void,
	onError: (err: string) => void
): () => void {
	const params = new URLSearchParams({ repo_url: repoUrl, query, session_id: sessionId });
	const es = new EventSource(`${BASE_URL}/api/chat/?${params.toString()}`);
	let finished = false;

	es.onmessage = (e) => {
		const data = JSON.parse(e.data);
		const token: string = data.message;
		onToken(token);
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
