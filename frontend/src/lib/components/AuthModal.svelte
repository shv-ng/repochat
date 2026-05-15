<script lang="ts">
	import { login, register } from '$lib/api';

	let { onClose }: { onClose: () => void } = $props();

	let mode = $state<'login' | 'register'>('login');
	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			if (mode === 'register') {
				await register(username, password);
			}
			await login(username, password);
			onClose();
		} catch (e: any) {
			error = e.message ?? 'Something went wrong';
		} finally {
			loading = false;
		}
	}
</script>

<div class="w-full max-w-sm bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl">
	<!-- Header -->
	<div class="mb-6">
		<div class="flex items-center gap-2 mb-1">
			<div class="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center text-white font-bold text-xs">R</div>
			<span class="font-semibold text-zinc-100">RepoChat</span>
		</div>
		<p class="text-zinc-400 text-sm">
			{mode === 'login' ? 'Sign in to save your chat sessions.' : 'Create an account to get started.'}
		</p>
	</div>

	<!-- Tabs -->
	<div class="flex bg-zinc-800 rounded-lg p-1 mb-6">
		<button
			class="flex-1 text-sm py-1.5 rounded-md transition-colors font-medium {mode === 'login' ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'}"
			onclick={() => { mode = 'login'; error = ''; }}
		>Login</button>
		<button
			class="flex-1 text-sm py-1.5 rounded-md transition-colors font-medium {mode === 'register' ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-400 hover:text-zinc-200'}"
			onclick={() => { mode = 'register'; error = ''; }}
		>Register</button>
	</div>

	<!-- Form -->
	<form onsubmit={handleSubmit} class="flex flex-col gap-4">
		<div>
			<label class="block text-xs font-medium text-zinc-400 mb-1.5" for="username">Username</label>
			<input
				id="username"
				type="text"
				bind:value={username}
				placeholder="your_username"
				required
				class="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder:text-zinc-500 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500 transition-colors"
			/>
		</div>
		<div>
			<label class="block text-xs font-medium text-zinc-400 mb-1.5" for="password">Password</label>
			<input
				id="password"
				type="password"
				bind:value={password}
				placeholder="••••••••"
				required
				class="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 placeholder:text-zinc-500 rounded-lg px-3 py-2 text-sm outline-none focus:border-indigo-500 transition-colors"
			/>
		</div>

		{#if error}
			<p class="text-red-400 text-xs bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{error}</p>
		{/if}

		<button
			type="submit"
			disabled={loading}
			class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 rounded-lg text-sm transition-colors"
		>
			{loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
		</button>
	</form>

	<!-- Close -->
	<button
		onclick={onClose}
		class="mt-4 w-full text-center text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
	>
		Continue without account
	</button>
</div>
