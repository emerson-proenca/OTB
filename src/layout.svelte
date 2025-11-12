<script>
    import Navbar from './components/Navbar.svelte';
    import Footer from './components/Footer.svelte';

    // Os blocos do Jinja2 se tornam propriedades (props) se você precisar
    // de metadados dinâmicos, mas para este teste, vamos fixar o básico.
    export let title = "OTB"; 
    export let metaDescription = "Over The Board Chess Tournaments";
</script>

<div 
    class="page"
    data-bs-theme="dark"
    data-bs-theme-base="gray"
    data-bs-theme-primary="purple"
>
    <Navbar /> 
    
    <div class="page-wrapper">
        <div class="container-xl">
            <slot /> 
        </div>
    </div>
</div>

<Footer />