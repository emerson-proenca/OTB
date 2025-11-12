<script lang="ts">
  // Definição da Interface (Tipo) para garantir segurança e autocompletar
  interface Tournament {
    regulation: string; // Link principal
    banner_url: string | null;
    title: string;
    start_date: string | null;
    place: string | null;
    time_control: string | null;
    club_logo: string | null;
    organizer: string | null;
    rating: string | null; // Rating, como FIDE, CBX, etc.
  }
  
  // A propriedade 'tournament' é requerida
  export let tournament: Tournament;

  // Variável reativa para a URL da imagem (incluindo o fallback estático)
  $: bannerUrl = tournament.banner_url || '/t-no-banner.jpg';
  $: clubLogoUrl = tournament.club_logo || '/t-no-club.jpg';
</script>

<a
  href={tournament.regulation}
  class="card card-link text-reset text-decoration-none position-relative d-flex flex-column"
  target="_blank"
  rel="noopener noreferrer"
  aria-label="Abrir página do torneio"
>
  <img
    class="card-img-top tournament-banner"
    src={bannerUrl}
    alt="Tournament Image"
  />

  <span
    class="position-absolute top-0 end-0 m-2"
    role="button"
    tabindex="0"
    aria-label="Salvar torneio"
    on:click|preventDefault={(e) => { 
      // Lógica para salvar o torneio.
      // e.stopPropagation() é importante para que o clique não abra o link <a>
      e.stopPropagation(); 
      alert('Torneio Salvo!');
    }}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="text-warning"
      aria-hidden="true"
    >
      <path
        d="M12 .587l3.668 7.431L23.4 9.75l-5.7 5.556L19.336 24 12 20.013 4.664 24 6.3 15.306 0.6 9.75l7.732-1.732L12 .587z"
      />
    </svg>
  </span>

  <div class="card-body d-flex flex-column">
    <h3 class="card-title mb-2 truncate-2">{tournament.title}</h3>

    <div class="text-secondary small">
      <div class="d-flex align-items-center mb-1">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="me-2 text-primary"
          aria-hidden="true"
        >
          <path
            d="M17 3.34a10 10 0 1 1 -14.995 8.984l-.005-.324l.005-.324a10 10 0 0 1 14.995-8.336zm-5 2.66v5l3 3"
          />
        </svg>
        <span class="fw-bold truncate-1">{tournament.start_date || "Não informado"}</span>
      </div>

      <div class="d-flex align-items-center mb-1">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="me-2 text-danger"
          aria-hidden="true"
        >
          <path
            d="M18.364 4.636a9 9 0 0 1 .203 12.519l-.203.21l-4.243 4.242a3 3 0 0 1 -4.097 .135l-4.244-4.243a9 9 0 0 1 12.728-12.728zm-6.364 3.364a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"
          />
        </svg>
        <span class="fw-bold truncate-1">{tournament.place || "Não informado"}</span>
      </div>

      <div class="d-flex align-items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="me-2 text-success"
          aria-hidden="true"
        >
          <path
            d="M17 2a2 2 0 0 1 1.995 1.85l.005.15v2a7 7 0 0 1-3.393 6 7 7 0 0 1 3.388 5.728l.005.272v2a2 2 0 0 1-1.85 1.995l-.15.005h-10a2 2 0 0 1-1.995-1.85l-.005-.15v-2a7 7 0 0 1 3.393-6 7 7 0 0 1-3.388-5.728l-.005-.272v-2a2 2 0 0 1 1.85-1.995l.15-.005h10z"
          />
        </svg>
        <span class="fw-bold truncate-1">{tournament.time_control || "Não informado"}</span>
      </div>
    </div>
  </div>

  <div
    class="card-footer d-flex align-items-center justify-content-between flex-wrap gap-2"
  >
    <div class="d-flex align-items-center flex-shrink-1 min-w-0">
      <img
        src={clubLogoUrl}
        alt="Club Logo"
        class="rounded-circle me-2 flex-shrink-0"
        width="32"
        height="32"
      />
      <div class="small text-truncate" style="max-width: 140px">
        <div class="fw-bold truncate-1">{tournament.organizer || "Não informado"}</div>
      </div>
    </div>

    <div class="d-flex flex-wrap justify-content-end gap-2 flex-grow-1">
      {#if tournament.rating}
        <span class="badge bg-info text-light truncate-1">
          {tournament.rating}
        </span>
      {/if}
    </div>
  </div>
</a>