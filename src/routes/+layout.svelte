<script lang="ts">
  import Navbar from '../components/Navbar.svelte';
  import Footer from '../components/Footer.svelte';
</script>

<svelte:head>
  <link 
    rel="stylesheet" 
    href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css" 
    id="style-tabler"
  />
  
  <script src="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/js/tabler.min.js"></script>
</svelte:head>

<div class="page">
    <header class="navbar navbar-expand-md d-print-none">
        <Navbar user={null} /> 
        </header>

    <div class="page-wrapper">
        <div class="page-body">
            <div class="container-xl">
                <slot /> 
            </div>
        </div>

        <Footer />
    </div>
</div>