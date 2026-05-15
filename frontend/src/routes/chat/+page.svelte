<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
  import { marked } from 'marked';
	import { Input } from '$lib/components/ui/input';
	import { Separator } from '$lib/components/ui/separator';
	import { streamChat } from '$lib/api';
	import { repoUrl, messages, isIngested } from '$lib/stores';
	import { get } from 'svelte/store';
	import type { Message } from '$lib/stores';

	let question =$state( '');
	let isStreaming =$state( false);
	let chatEl: HTMLDivElement;

	const repo = get(repoUrl);
    let sid: string;

	onMount(() => {
		if (!get(isIngested) || !repo) {
			goto('/');
            return;
		}
        const storageKey = 'session_' + repo;
        sid = localStorage.getItem(storageKey) ?? crypto.randomUUID();
        localStorage.setItem(storageKey, sid);
	});

	async function scrollToBottom() {
		await tick();
		chatEl?.scrollTo({ top: chatEl.scrollHeight, behavior: 'smooth' });
	}

  async function sendMessage() {
    const q = question.trim();
    if (!q || isStreaming) return;
    question = '';  // clear immediately on send

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: q };
    const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: '', streaming: true };

    messages.update((m) => [...m, userMsg, assistantMsg]);
    isStreaming = true;
    await scrollToBottom();

    streamChat(
        repo, q, sid,
        (token) => {
            messages.update((m) => {
                const last = m[m.length - 1];
                if (last.role === 'assistant') return [...m.slice(0, -1), { ...last, content: last.content + token }];
                return m;
            });
            scrollToBottom();
        },
        () => {
            messages.update((m) => {
                const last = m[m.length - 1];
                if (last.role === 'assistant') return [...m.slice(0, -1), { ...last, streaming: false }];
                return m;
            });
            isStreaming = false;  // ← re-enables input
            scrollToBottom();
        },
        (err) => {
            messages.update((m) => {
                const last = m[m.length - 1];
                if (last.role === 'assistant') return [...m.slice(0, -1), { ...last, content: `Error: ${err}`, streaming: false }];
                return m;
            });
            isStreaming = false;
        }
    );
}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	function resetSession() {
		messages.set([]);
		isIngested.set(false);
		goto('/');
	}
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
	<!-- Top Bar -->
	<header class="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-10">
		<div class="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
			<div class="flex items-center gap-3 min-w-0">
				<div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
					R
				</div>
				<div class="min-w-0">
					<p class="text-xs text-zinc-500 font-medium uppercase tracking-wide">Repository</p>
					<p class="text-sm text-zinc-200 truncate font-mono">{repo}</p>
				</div>
			</div>
			<Button
				variant="ghost"
				onclick={resetSession}
				class="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 text-sm shrink-0"
			>
				← Change Repo
			</Button>
		</div>
	</header>

	<!-- Chat Messages -->
	<div
		bind:this={chatEl}
		class="flex-1 overflow-y-auto px-4 py-8"
	>
		<div class="max-w-3xl mx-auto flex flex-col gap-6">
			{#if $messages.length === 0}
				<!-- Empty state -->
				<div class="text-center py-20">
					<div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4">
						<svg class="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-3.037-.476 5.977 5.977 0 01-4.13 1.446.75.75 0 01-.574-1.227 4.507 4.507 0 001.063-1.997A8.196 8.196 0 013 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
						</svg>
					</div>
					<h2 class="text-lg font-semibold text-zinc-300 mb-1">Ask about the codebase</h2>
					<p class="text-zinc-500 text-sm">Try: "How does authentication work?" or "Explain the main entry point"</p>
				</div>
			{/if}

			{#each $messages as msg (msg.id)}
				{#if msg.role === 'user'}
					<!-- User message -->
					<div class="flex justify-end">
						<div class="max-w-[80%] bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
							{msg.content}
						</div>
					</div>
				{:else}
					<!-- Assistant message -->
					<div class="flex gap-3 items-start">
						<div class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-indigo-400 shrink-0 mt-0.5">
							AI
						</div>
<!-- assistant message content, replace the text div -->
<div class="flex-1 min-w-0">
    <div class="text-sm leading-relaxed text-zinc-200 prose prose-invert prose-sm max-w-none
                prose-code:bg-zinc-800 prose-code:px-1 prose-code:rounded
                prose-pre:bg-zinc-800 prose-pre:border prose-pre:border-zinc-700">
        {#if msg.content}
            {@html marked(msg.content)}
        {:else}
            <span class="inline-flex gap-1 items-center text-zinc-500">
                <span class="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </span>
        {/if}
        {#if msg.streaming}
            <span class="inline-block w-0.5 h-4 bg-indigo-400 animate-pulse ml-0.5 align-middle"></span>
        {/if}
    </div>
</div>
					</div>
				{/if}
			{/each}
		</div>
	</div>

	<!-- Input Bar -->
	<div class="border-t border-zinc-800 bg-zinc-900/80 backdrop-blur sticky bottom-0">
		<div class="max-w-3xl mx-auto px-4 py-4">
			<div class="flex items-center gap-3 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2 focus-within:border-indigo-500 transition-colors">
				<input
					type="text"
					placeholder="Ask anything about this repository..."
					bind:value={question}
					onkeydown={handleKeydown}
					disabled={isStreaming}
					class="flex-1 bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 outline-none disabled:opacity-50"
				/>
				<button
					onclick={sendMessage}
					disabled={isStreaming || !question.trim()}
					class="w-8 h-8 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors shrink-0"
				>
					{#if isStreaming}
						<svg class="w-3.5 h-3.5 text-white animate-spin" viewBox="0 0 24 24" fill="none">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
						</svg>
					{:else}
						<svg class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
						</svg>
					{/if}
				</button>
			</div>
			<p class="text-xs text-zinc-600 text-center mt-2">Press Enter to send · Shift+Enter for newline</p>
		</div>
	</div>
</div>
