export const theme = {
    colors: {
        primary: "#00ff7f",       // Neon Green
        primaryLight: "#00ff7f",  // Added to fix NullPointerException
        primaryDark: "#00cc66",
        secondary: "#00e5ff",     // Cyan/Cyber Blue
        accent: "#7000ff",        // Deep Purple
        background: "#050510",    // Deep Space Black
        surface: "#101025",       // Dark Blue-Black Surface
        surfaceLight: "#1c1c3d",  // Lighter Surface for cards
        text: "#ffffff",
        textSecondary: "#a0a0b0",
        muted: "#404050",
        danger: "#ff3366",        // Neon Red/Pink
        success: "#00ff7f",
        warning: "#ffaa00",
        info: "#00e5ff",
        transparent: "transparent",
        glass: "rgba(20, 20, 40, 0.7)", // Glassmorphism base
        glassBorder: "rgba(255, 255, 255, 0.1)"
    },
    gradients: {
        main: ["#050510", "#101025"] as const,
        card: ["#1c1c3d", "#101025"] as const,
        primary: ["#00ff7f", "#00cc66"] as const,
        danger: ["#ff3366", "#cc0044"] as const,
        glass: ["#1e1e3c99", "#14142866"] as const // Converted to HEX+Alpha for stability
    },
    spacing: {
        s: 8,
        m: 16,
        l: 24,
        xl: 32
    },
    borderRadius: {
        s: 8,
        m: 16,
        l: 24
    }
};
