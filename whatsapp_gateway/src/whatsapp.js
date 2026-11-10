import makeWASocket, {
    DisconnectReason,
    useMultiFileAuthState,
    fetchLatestBaileysVersion
} from '@whiskeysockets/baileys';
import pino from 'pino';
import qrcode from 'qrcode-terminal';
import fs from 'fs';
import path from 'path';
import { config } from './config.js';

class WhatsAppManager {
    constructor() {
        this.sock = null;
        this.isConnected = false;
        this.latestQr = null;
        this.userInfo = null;
        this.isConnecting = false;
    }

    async init() {
        const sessionPath = path.resolve(config.SESSION_DIR);
        if (!fs.existsSync(sessionPath)) {
            fs.mkdirSync(sessionPath, { recursive: true });
        }

        const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
        const { version } = await fetchLatestBaileysVersion();

        const logger = pino({ level: 'silent' });

        this.sock = makeWASocket({
            version,
            logger,
            printQRInTerminal: false,
            auth: state,
            browser: ['OTP-Verification-Service', 'Chrome', '1.0.0'],
            generateHighQualityLinkPreview: true,
            syncFullHistory: false
        });

        this.sock.ev.on('creds.update', saveCreds);

        this.sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                this.latestQr = qr;
                console.log('\n==================================================');
                console.log('📌 SCAN THIS QR CODE WITH WHATSAPP TO CONNECT:');
                console.log('==================================================\n');
                qrcode.generate(qr, { small: true });
                console.log('\n💡 Tip: You can also view the QR code in your browser at:');
                console.log(`   http://localhost:${config.PORT}/api/qr\n`);
            }

            if (connection === 'close') {
                this.isConnected = false;
                this.userInfo = null;
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

                console.log(`⚠️ WhatsApp connection closed (Reason code: ${statusCode}). Reconnecting: ${shouldReconnect}`);

                if (statusCode === DisconnectReason.loggedOut) {
                    console.log('❌ Device logged out. Clearing auth credentials...');
                    try {
                        fs.rmSync(sessionPath, { recursive: true, force: true });
                    } catch (e) {
                        console.error('Error removing session directory:', e);
                    }
                    setTimeout(() => this.init(), 3000);
                } else if (shouldReconnect) {
                    setTimeout(() => this.init(), 3000);
                }
            } else if (connection === 'open') {
                this.isConnected = true;
                this.latestQr = null;
                this.userInfo = this.sock.user;
                console.log('\n==================================================');
                console.log('✅ WHATSAPP CONNECTED SUCCESSFULLY!');
                console.log(`📱 Connected as: ${this.sock.user?.id || 'WhatsApp User'}`);
                console.log('🚀 Ready to send OTP messages!');
                console.log('==================================================\n');
            }
        });
    }

    async sendMessage(phoneNumber, messageText) {
        if (!this.isConnected || !this.sock) {
            throw new Error('WhatsApp service is not connected. Please scan QR code first.');
        }

        const cleanDigits = String(phoneNumber).replace(/[^0-9]/g, '');
        const jid = `${cleanDigits}@s.whatsapp.net`;

        // Check if number exists on WhatsApp
        try {
            const [result] = await this.sock.onWhatsApp(jid);
            if (!result || !result.exists) {
                throw new Error(`The phone number ${phoneNumber} is not registered on WhatsApp.`);
            }
        } catch (e) {
            // If onWhatsApp check fails with network issue, we can still attempt sending
            console.warn(`[Warning] onWhatsApp check skipped/failed for ${jid}:`, e.message);
        }

        const sent = await this.sock.sendMessage(jid, {
            text: messageText
        });

        return {
            success: true,
            messageId: sent.key.id,
            timestamp: sent.messageTimestamp,
            to: cleanDigits
        };
    }

    getStatus() {
        return {
            connected: this.isConnected,
            user: this.userInfo,
            hasQr: !!this.latestQr,
            timestamp: Date.now()
        };
    }

    getQr() {
        return this.latestQr;
    }
}

export const whatsappManager = new WhatsAppManager();
