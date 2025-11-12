<script lang="ts">
  // Definição da Interface (Tipo) do objeto de usuário para evitar o erro 'never'
  interface CurrentUser {
    username: string;
    profile_picture: string | null;
    role: string;
  }

  // A propriedade 'user' é do tipo CurrentUser OU null
  export let user: CurrentUser | null = null;

  // Lógica Reativa Svelte
  // 1. URL da imagem de perfil
  $: profilePictureUrl = user && user.profile_picture
    ? user.profile_picture
    : '/static/avatar.jpg';

  // 2. Link do perfil (usado no desktop e no mobile dropdown)
  $: profileLink = user && user.username
    ? `/@/${user.username}/`
    : '#';
</script>


<div class="sticky-top">
  <header class="navbar navbar-expand-md">
    <div class="container-xl">
      <div
        class="d-flex d-md-none w-100 align-items-center justify-content-between py-2"
      >
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mobileMenu"
          aria-controls="mobileMenu"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="icon icon-tabler icons-tabler-outline icon-tabler-menu-2"
          >
            <path stroke="none" d="M0 0h24v24H0z" fill="none" />
            <path d="M4 6l16 0" />
            <path d="M4 12l16 0" />
            <path d="M4 18l16 0" />
          </svg>
        </button>

        <a class="navbar-brand mx-2" href="/">
          <img
            src="/otb.svg"
            alt="(ChessBoard) OTB"
            class="navbar-brand-image"
            style="width: 64px; height: auto"
          />
        </a>

        <div class="dropdown">
          {#if user}
            <a href="/" class="nav-link p-0" title="Profile" data-bs-toggle="dropdown">
              <span
                class="avatar avatar-sm"
                style="background-image: url({profilePictureUrl})"
              ></span>
            </a>
            <div class="dropdown-menu dropdown-menu-end dropdown-menu-arrow">
              <a href={profileLink} class="dropdown-item">Profile</a>
              <a href="/settings" class="dropdown-item">Settings</a>
              <a href="/sign-in" class="dropdown-item">Logout</a>
            </div>
          {:else}
            <a href="/login" class="btn btn-outline-primary d-sm-block d-none">Login</a>
          {/if}
        </div>
      </div>
      <div class="collapse d-md-none mt-2" id="mobileMenu">
        <ul class="navbar-nav">
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/" data-bs-toggle="dropdown" aria-expanded="false">
              Tournaments
            </a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="/tournaments">All Tournaments</a></li>
              <li><a class="dropdown-item" href="/calendar">Calendar</a></li>
              <li><a class="dropdown-item" href="/maps-vector">Map Vector</a></li>
            </ul>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/" data-bs-toggle="dropdown" aria-expanded="false">
              Players
            </a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="/players">All Players</a></li>
              <li><a class="dropdown-item" href="/ranking">Ranking</a></li>
            </ul>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/" data-bs-toggle="dropdown" aria-expanded="false">
              Clubs
            </a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="/broadcast">Broadcast</a></li>
            </ul>
          </li>
        </ul>
      </div>

      <div class="d-none d-md-flex">
        <a class="navbar-brand mx-2" href="/">
          <img
            src="/otb.svg"
            alt="(ChessBoard) OTB"
            class="navbar-brand-image"
            style="width: 64px; height: auto"
          />
        </a>
      </div>

      <div class="collapse navbar-collapse d-none d-md-flex" id="desktopMenu">
        <ul class="navbar-nav">
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/" data-bs-toggle="dropdown" data-bs-auto-close="outside">
              <span class="nav-link-title">Tournaments</span>
            </a>
            <div class="dropdown-menu">
              <a class="dropdown-item" href="/tournaments">All Tournaments</a>
              <a class="dropdown-item" href="/calendar">Calendar</a>
              <a class="dropdown-item" href="/maps-vector">Map Vector</a>
            </div>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/" data-bs-toggle="dropdown" data-bs-auto-close="outside">
              <span class="nav-link-title">Players</span>
            </a>
            <div class="dropdown-menu">
              <a class="dropdown-item" href="/players">All Players</a>
              <a class="dropdown-item" href="/ranking">Ranking</a>
            </div>
          </li>
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="/" data-bs-toggle="dropdown" data-bs-auto-close="outside">
              <span class="nav-link-title">Clubs</span>
            </a>
            <div class="dropdown-menu">
              <a class="dropdown-item" href="/broadcast">Broadcast</a>
            </div>
          </li>
        </ul>

        <ul class="navbar-nav ms-auto align-items-center">
          <li class="nav-item dropdown">
            {#if user}
              <a
                href="/"
                class="nav-link d-flex lh-1 p-0 px-2"
                data-bs-toggle="dropdown"
              >
                <span
                  class="avatar avatar-sm"
                  style="background-image: url({profilePictureUrl})"
                ></span>
                <div class="d-none d-xl-block ps-2">
                  <div>{user.username}</div>
                  <div class="mt-1 small text-secondary">
                    {user.role || "Player"}
                  </div>
                </div>
              </a>
              <div class="dropdown-menu dropdown-menu-end dropdown-menu-arrow">
                <a href={profileLink} class="dropdown-item">Profile</a>
                <a href="/settings" class="dropdown-item">Settings</a>
                <a href="/sign-in" class="dropdown-item">Logout</a>
              </div>
            {:else}
              <a href="/login" class="btn btn-outline-primary">Login</a>
            {/if}
          </li>
        </ul>
      </div>
    </div>
  </header>
</div>