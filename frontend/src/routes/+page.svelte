<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { ingestRepo, watchIngestStatus } from '$lib/api';
	import { repoUrl, isIngested, accessToken } from '$lib/stores';
	import { get } from 'svelte/store';
	import { onMount } from 'svelte';
	import { PUBLIC_BASE_URL } from '$env/static/public';

	let url =$state( get(repoUrl) || '');
	let status =$state( '');
	let loading =$state( false);
	let error =$state( '');
	let prevRepos =$state<{id: number, url: string}[]>([]);

    async function fetchPrevRepos() {
        const token = get(accessToken);
        if (!token) return;

        try {
            const res = await fetch(`${PUBLIC_BASE_URL}/api/repos/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                prevRepos = await res.json();
            }
        } catch (e) {
            console.error('Failed to fetch prev repos', e);
        }
    }

    onMount(fetchPrevRepos);

	async function handleIngest() {
		if (!url.trim()) return;
		error = '';
		loading = true;
		status = 'Starting...';
		repoUrl.set(url.trim());

		try {
			const taskId = await ingestRepo(url.trim());
			watchIngestStatus(
				taskId,
				(s) => (status = s),
				async () => {
					isIngested.set(true);
					loading = false;
                    await fetchPrevRepos();
					goto('/chat');
				},
				(err) => {
					error = err;
					loading = false;
					status = '';
				}
			);
		} catch (e) {
			error = 'Failed to connect to backend. Is it running?';
			loading = false;
			status = '';
		}
	}

    function selectRepo(r: string) {
        repoUrl.set(r);
        isIngested.set(true);
        goto('/chat');
    }
</script>

<div class="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-center px-4">
	<!-- Logo / Header -->
	<div class="mb-12 text-center">
		<div class="flex items-center justify-center gap-3 mb-4">
			<div class="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center text-white font-bold text-lg">
				R
			</div>
			<h1 class="text-3xl font-bold tracking-tight">RepoChat</h1>
		</div>
		<p class="text-zinc-400 text-base max-w-sm">
			Paste a GitHub repository URL to index it, then ask questions about the codebase.
		</p>
	</div>

	<!-- Card -->
	<div class="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl">
		<label class="block text-sm font-medium text-zinc-300 mb-2" for="repo-url">
			GitHub Repository URL
		</label>
		<Input
			id="repo-url"
			type="url"
			placeholder="https://github.com/owner/repo"
			bind:value={url}
			disabled={loading}
			class="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-indigo-500 mb-4"
			onkeydown={(e) => e.key === 'Enter' && handleIngest()}
		/>

    <Button
      onclick={handleIngest}
      disabled={loading || !url.trim()}
      class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors"
    >
      {#if loading}
        <span class="flex items-center gap-2">
          <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          {status || 'Starting...'}
        </span>
      {:else}
        Ingest Repository →
      {/if}
    </Button>

    <!-- Status / Error -->
    {#if status && !error}
      <div class="mt-4 flex items-center gap-2 text-sm text-zinc-400">
        <span class="inline-block w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
        {status}
      </div>
    {/if}

    {#if error}
      <div class="mt-4 text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
        {error}
      </div>
    {/if}
  </div>

    {#if prevRepos.length > 0}
      <div class="w-full max-w-lg mt-8">
          <h3 class="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-4">Previously Ingested</h3>
          <div class="grid gap-2">
              {#each prevRepos as repo}
                  <button onclick={() => selectRepo(repo.url)} class="text-left w-full bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl px-4 py-3 flex items-center justify-between group transition-colors">
                      <span class="text-sm text-zinc-300 font-mono group-hover:text-indigo-400">{repo.url}</span>
                      <svg class="w-4 h-4 text-zinc-600 group-hover:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                  </button>
              {/each}
          </div>
      </div>
    {/if}

  <p class="mt-8 text-xs text-zinc-600">
    Supports public GitHub repos. Large repos may take a moment to index.
  </p>
</div>
