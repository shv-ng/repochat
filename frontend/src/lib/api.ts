import { PUBLIC_BASE_URL } from '$env/static/public';
import { accessToken, refreshToken as refreshTokenStore } from '$lib/stores';
import { get } from 'svelte/store';

const BASE_URL = PUBLIC_BASE_URL;

export async function login(username: string, password: string) {
	const res = await fetch(`${BASE_URL}/api/auth/token/`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ username, password })
	});
	if (!res.ok) throw new Error('Login failed');
	const { access, refresh } = await res.json();
	accessToken.set(access);
	refreshTokenStore.set(refresh);
}

export async function register(username: string, password: string) {
	const res = await fetch(`${BASE_URL}/api/auth/register/`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ username, password })
	});
	if (!res.ok) throw new Error('Registration failed');
	return await res.json();
}

export async function refreshToken() {
	const refresh = get(refreshTokenStore);
	if (!refresh) throw new Error('No refresh token');

	const res = await fetch(`${BASE_URL}/api/auth/refresh/`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ refresh })
	});
	if (!res.ok) throw new Error('Token refresh failed');
	const { access } = await res.json();
	accessToken.set(access);
}

export async function ingestRepo(repoUrl: string): Promise<string> {
    const token = get(accessToken);
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

	const res = await fetch(`${BASE_URL}/api/ingest/`, {
		method: 'POST',
		headers,
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
	let aborted = false;
	const controller = new AbortController();

	const run = async () => {
		const params = new URLSearchParams({ repo_url: repoUrl, query, session_id: sessionId });
		const token = get(accessToken);
		const headers: HeadersInit = {};
		if (token) headers['Authorization'] = `Bearer ${token}`;

		try {
			const res = await fetch(`${BASE_URL}/api/chat/?${params.toString()}`, {
				headers,
				signal: controller.signal
			});

			if (!res.ok) throw new Error('Chat request failed');
			if (!res.body) throw new Error('No response body');

			const reader = res.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done || aborted) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() ?? '';  // keep incomplete line

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const raw = line.slice(6).trim();
						if (!raw) continue;
						try {
							const parsed = JSON.parse(raw);
							const msg = parsed.message ?? parsed;
							if (typeof msg === 'string' && msg) onToken(msg);
						} catch {
							// skip malformed
						}
					}
				}
			}

			if (!aborted) onDone();
		} catch (err: any) {
			if (!aborted) onError(err.message ?? 'Chat failed');
		}
	};

	run();
	return () => {
		aborted = true;
		controller.abort();
	};
}

export async function getChatHistory(sessionId: string) {
	const res = await fetch(`${BASE_URL}/api/chat/history/?session_id=${sessionId}`);
	if (!res.ok) throw new Error('Failed to fetch chat history');
	return await res.json();
}
