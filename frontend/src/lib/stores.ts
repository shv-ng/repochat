import { writable } from 'svelte/store';

export type Message = {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	streaming?: boolean;
};

export const repoUrl = writable<string>('');
export const sessionId = writable<string>(crypto.randomUUID());
export const messages = writable<Message[]>([]);
export const isIngested = writable<boolean>(false);
export const accessToken = writable<string | null>(null);
export const refreshToken = writable<string | null>(null);
