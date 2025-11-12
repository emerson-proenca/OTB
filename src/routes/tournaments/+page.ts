// Simula a busca dos dados da lista de torneios
export async function load({ fetch }) {
  // Você substituirá esta lógica pela sua chamada de API real
  const tournaments = [
    {
      id: 1,
      name: "Open Chess Championship",
      date: "2025-12-01",
      location: "City A",
      imageUrl: "/path/to/img1.jpg",
      description: "Major annual event.",
    },
    {
      id: 2,
      name: "Summer Blitz Cup",
      date: "2025-12-15",
      location: "City B",
      imageUrl: "/path/to/img2.jpg",
      description: "Fast-paced fun.",
    },
    {
      id: 3,
      name: "Youth Masters 2026",
      date: "2026-01-10",
      location: "City C",
      imageUrl: "/path/to/img3.jpg",
      description: "For players under 18.",
    },
    // ... mais torneios
  ];

  return {
    tournaments: tournaments,
    // Metadados são passados aqui e consumidos no +page.svelte
    meta: {
      title: "OTB - Tournaments",
      description:
        "Browse all chess tournaments and events on Over The Board platform.",
    },
  };
}
