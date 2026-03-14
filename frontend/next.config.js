const withPWA = require('next-pwa')({
    dest: 'public',
    disable: process.env.NODE_ENV === 'development',
    register: true,
    skipWaiting: true,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    images: {
        domains: ['www.mako.co.il', 'www.ynet.co.il', 'www.haaretz.co.il', 'www.israelhayom.co.il', 'www.kan.org.il', 'www.aljazeera.com', 'm.psecn.photoshelter.com', 'ichef.bbci.co.uk'],
    },
    // Silence the Turbopack warning caused by next-pwa's webpack config injection
    turbopack: {}
};

module.exports = withPWA(nextConfig);
