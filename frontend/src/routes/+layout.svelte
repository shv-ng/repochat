<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { accessToken, refreshToken as refreshStore } from '$lib/stores';
	import { refreshToken } from '$lib/api';
	import { onMount } from 'svelte';
	import AuthModal from '$lib/components/AuthModal.svelte';

	let { children } = $props();
	let showModal = $state(false);

	onMount(async () => {
		if ($refreshStore) {
			try {
				await refreshToken();
			} catch (e) {
				refreshStore.set(null);
			}
		}
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="fixed top-0 right-0 p-4 z-50">
	{#if $accessToken}
		<button
			class="bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-200 px-4 py-2 rounded-lg text-sm transition-colors"
			onclick={() => { accessToken.set(null); refreshStore.set(null); }}
		>
			Logout
		</button>
	{:else}
		<button
			class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
			onclick={() => showModal = true}
		>
			Login
		</button>
	{/if}
</div>

{#if showModal}
	<div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
		<AuthModal onClose={() => showModal = false} />
	</div>
{/if}

<main>
	{@render children()}
</main>
