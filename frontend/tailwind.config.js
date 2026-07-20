/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Design tokens for the Wantok Lender field dashboard.
        // Grounded in the ledger book / kina-shell trading register the
        // platform is digitizing — legible in bright sunlight on cheap
        // screens, not a generic SaaS palette.
        ledger: {
          paper: "#F3EEE1",     // aged ledger-paper background
          ink: "#211C14",       // near-black warm ink for body text
          rule: "#C9BFA3",      // faint ruled-line grey-tan for dividers
        },
        kina: {
          gold: "#B8863B",      // kina-shell gold — primary accent / positive
          deep: "#5C3E1E",      // dark bark-brown — headers, emphasis
        },
        bilum: {
          teal: "#1E5450",      // woven-bilum teal — secondary accent, links
        },
        risk: {
          none: "#3F7A4E",
          watch: "#C68A2E",
          high: "#A5342B",
        },
      },
      fontFamily: {
        display: ["'Barlow Condensed'", "sans-serif"],  // dense numerals, scannable at a glance
        body: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
