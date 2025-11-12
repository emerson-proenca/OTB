<script lang="ts">
  import Card from '../../components/Card.svelte';
  import { setContext } from 'svelte';

  // Recebe os dados carregados pela função load
  export let data;

  // Usa setContext ou uma tag <svelte:head> para metadados

  // O componente Card agora está em $lib/components/Card.svelte.
</script>

<svelte:head>
  <title>{data.meta.title}</title>
  <meta name="description" content={data.meta.description} />
</svelte:head>

<div class="page-header d-print-none">
  <h1 class="page-title">Chess Tournaments</h1>
</div>

<div class="row row-cards">
  {#each data.tournaments as tournament (tournament.id)}
    <div class="col-12 col-md-6 col-lg-4 col-xl-3">
      <Card {tournament} />
    </div>
  {/each}
  </div>