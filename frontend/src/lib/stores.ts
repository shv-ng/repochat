import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Message = {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	streaming?: boolean;
};

export const repoUrl = writable<string>(browser ? localStorage.getItem('repoUrl') ?? '' : '');
repoUrl.subscribe((v) => browser && localStorage.setItem('repoUrl', v));

export const messages = writable<Message[]>([]);
export const isIngested = writable<boolean>(false);

export const accessToken = writable<string | null>(
    browser ? localStorage.getItem('accessToken') : null
);
accessToken.subscribe((v) => browser && (v ? localStorage.setItem('accessToken', v) : localStorage.removeItem('accessToken')));

export const refreshToken = writable<string | null>(
    browser ? localStorage.getItem('refreshToken') : null
);
refreshToken.subscribe((v) => browser && (v ? localStorage.setItem('refreshToken', v) : localStorage.removeItem('refreshToken')));
