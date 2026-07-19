import React, { useState } from 'react';
import GridScan from './GridScan';

export default function Login() {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#05161A' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1 }}>
        <GridScan
          sensitivity={0.55}
          lineThickness={1}
          linesColor="#1B353E"
          gridScale={0.1}
          scanColor="#FF9FFC"
          scanOpacity={0.4}
          enablePost
          bloomIntensity={0.6}
          chromaticAberration={0.002}
          noiseIntensity={0.01}
        />
      </div>
      
      <div style={{ position: 'relative', zIndex: 10, background: 'rgba(12, 29, 34, 0.85)', backdropFilter: 'blur(20px)', border: '1px solid rgba(27, 53, 62, 0.6)', borderRadius: '20px', padding: '48px 36px', boxShadow: '0 25px 60px rgba(0,0,0,0.4)', width: '100%', maxWidth: '420px', color: '#E2E8F0', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '2.8rem', marginBottom: '12px' }}>⚡</div>
          <h2 style={{ fontWeight: '800', marginBottom: '6px', fontSize: '1.6rem', color: '#03EF62' }}>Welcome Back</h2>
          <p style={{ margin: 0, fontSize: '0.92rem', color: '#6B7280' }}>Log in to continue your learning streak.</p>
        </div>
        
        <form method="POST" action="/login">
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', fontSize: '0.88rem', marginBottom: '8px' }}>Username or Email</label>
            <input
              type="text"
              name="identifier"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              autoFocus
              placeholder="Enter your username or email"
              style={{ background: 'rgba(5, 22, 26, 0.9)', border: '1.5px solid #1B353E', borderRadius: '10px', padding: '12px 16px', width: '100%', fontSize: '0.94rem', color: '#E2E8F0', outline: 'none', boxSizing: 'border-box' }}
            />
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', fontSize: '0.88rem', marginBottom: '8px' }}>Password</label>
            <input
              type="password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
              style={{ background: 'rgba(5, 22, 26, 0.9)', border: '1.5px solid #1B353E', borderRadius: '10px', padding: '12px 16px', width: '100%', fontSize: '0.94rem', color: '#E2E8F0', outline: 'none', boxSizing: 'border-box' }}
            />
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                name="remember"
                id="remember"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                style={{ accentColor: '#03EF62', width: '1rem', height: '1rem' }}
              />
              <label htmlFor="remember" style={{ fontSize: '0.88rem', fontWeight: '500', cursor: 'pointer' }}>Remember me</label>
            </div>
            <a href="/forgot-password" style={{ color: '#03EF62', fontSize: '0.88rem', fontWeight: '600', textDecoration: 'none' }}>Forgot Password?</a>
          </div>
          
          <button
            type="submit"
            style={{ background: 'linear-gradient(135deg, #03EF62 0%, #10B981 100%)', border: 'none', borderRadius: '10px', color: '#05161A', fontWeight: '700', padding: '14px', width: '100%', fontSize: '0.95rem', cursor: 'pointer', transition: 'all 0.2s' }}
          >
            Log In →
          </button>
        </form>
        
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <p style={{ marginBottom: '8px', fontSize: '0.92rem' }}>Don't have an account? <a href="/register" style={{ color: '#03EF62', fontWeight: '700', textDecoration: 'none' }}>Sign up</a></p>
          <p style={{ fontSize: '0.78rem', margin: 0, color: '#6B7280' }}>Demo: admin@tarunsfxo.com / Admin@123</p>
        </div>
      </div>
    </div>
  );
}
