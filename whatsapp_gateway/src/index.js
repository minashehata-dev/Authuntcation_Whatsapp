import express from 'express';
import cors from 'cors';
import { config } from './config.js';
import { whatsappManager } from './whatsapp.js';

const app = express();

app.use(cors());
app.use(express.json());

// Token Authentication Middleware for internal endpoints
const verifyInternalToken = (req, res, next) => {
    const token = req.headers['x-internal-token'] || req.query.token;
    if (!token || token !== config.INTERNAL_TOKEN) {
        return res.status(401).json({
            success: false,
            message: 'Unauthorized: Invalid or missing X-Internal-Token header'
        });
    }
    next();
};

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        service: 'WhatsApp Baileys Gateway',
        status: 'running',
        connected: whatsappManager.isConnected
    });
});

// Status check endpoint (called by Python backend)
app.get('/api/status', (req, res) => {
    res.json(whatsappManager.getStatus());
});

// Browser-friendly QR Code display page
app.get('/api/qr', (req, res) => {
    const qr = whatsappManager.getQr();
    if (whatsappManager.isConnected) {
        return res.send(`
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="utf-8">
                <title>حالة الواتساب</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 40px; background: #f0f2f5; }
                    .card { background: white; border-radius: 12px; padding: 30px; max-width: 450px; margin: 0 auto; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
                    .badge { display: inline-block; padding: 8px 16px; border-radius: 20px; background: #25D366; color: white; font-weight: bold; margin-bottom: 15px; }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="badge">متصل بنجاح ✅</div>
                    <h2>الواتساب متصل ويعمل بكفاءة!</h2>
                    <p>أنت جاهز الآن لإرسال رسائل التحقق (OTP) من خلال النظام.</p>
                </div>
            </body>
            </html>
        `);
    }

    if (!qr) {
        return res.send(`
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="utf-8">
                <title>انتظار رمز QR</title>
                <meta http-equiv="refresh" content="3">
                <style>
                    body { font-family: sans-serif; text-align: center; padding: 50px; background: #f7f9fa; }
                    .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #25D366; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div class="spinner"></div>
                <h3>جاري توليد رمز الـ QR للواتساب...</h3>
                <p>سيتم تحديث الصفحة تلقائياً خلال ثوانٍ.</p>
            </body>
            </html>
        `);
    }

    const qrImgUrl = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qr)}&size=300x300&margin=10`;
    res.send(`
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="utf-8">
            <title>ربط الواتساب - امسح الرمز</title>
            <meta http-equiv="refresh" content="20">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 30px; background: #f0f2f5; }
                .card { background: white; border-radius: 16px; padding: 30px; max-width: 480px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
                img { border-radius: 12px; border: 1px solid #e1e4e8; margin: 20px 0; }
                .instructions { text-align: right; margin-top: 20px; font-size: 14px; color: #4a4a4a; line-height: 1.8; }
                ol { padding-right: 20px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>📱 ربط رقم الواتساب بالنظام</h2>
                <p>امسح رمز الـ QR التالي من تطبيق الواتساب على هاتفك:</p>
                <img src="${qrImgUrl}" alt="WhatsApp QR Code" width="280" height="280" />
                <div class="instructions">
                    <ol>
                        <li>افتح <strong>واتساب</strong> على هاتفك.</li>
                        <li>اضغط على <strong>القائمة (⋮)</strong> أو <strong>الإعدادات</strong>.</li>
                        <li>اختر <strong>الأجهزة المرتبطة (Linked Devices)</strong>.</li>
                        <li>اضغط على <strong>ربط جهاز (Link a Device)</strong> ووجه الكاميرا نحو الشاشة.</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
    `);
});

// Send Message Endpoint (Protected by internal token)
app.post('/api/send-message', verifyInternalToken, async (req, res) => {
    const { phone_number, message } = req.body;

    if (!phone_number || !message) {
        return res.status(400).json({
            success: false,
            message: 'phone_number and message fields are required'
        });
    }

    try {
        const result = await whatsappManager.sendMessage(phone_number, message);
        return res.json({
            success: true,
            message: 'Message delivered to WhatsApp socket',
            data: result
        });
    } catch (error) {
        return res.status(500).json({
            success: false,
            message: error.message || 'Failed to send WhatsApp message'
        });
    }
});

// Start server and initialize Baileys
app.listen(config.PORT, () => {
    console.log(`\n==================================================`);
    console.log(`🌐 Baileys Gateway Server running on port ${config.PORT}`);
    console.log(`🔗 Internal URL: http://localhost:${config.PORT}`);
    console.log(`==================================================\n`);
    whatsappManager.init().catch(err => {
        console.error('Fatal error initializing WhatsApp:', err);
    });
});
