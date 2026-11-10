import dotenv from 'dotenv';
dotenv.config();

export const config = {
    PORT: process.env.PORT || 3001,
    INTERNAL_TOKEN: process.env.INTERNAL_TOKEN || 'internal-baileys-secret-token-abcdef',
    SESSION_DIR: process.env.SESSION_DIR || './sessions/baileys_auth',
};
