# Modelo de Seguridad - CloudVault

## Resumen de Capas

```
┌─────────────────────────────────────────────────────────┐
│ CAPA 4: Acceso de Red                                   │
│   - Solo red local (sin puertos expuestos)              │
│   - Tailscale WireGuard (opcional, cifrado E2E)         │
├─────────────────────────────────────────────────────────┤
│ CAPA 3: Autenticacion                                   │
│   - Usuario/contrasena en Immich                        │
│   - Sesiones con timeout                                │
├─────────────────────────────────────────────────────────┤
│ CAPA 2: Cifrado en Transito                             │
│   - HTTP local (red confiable)                          │
│   - WireGuard (si usas Tailscale fuera de casa)         │
├─────────────────────────────────────────────────────────┤
│ CAPA 1: Cifrado en Reposo (Nubes)                       │
│   - AES-256 (archivos)                                  │
│   - Nombres de archivo cifrados                         │
│   - Estructura de carpetas cifrada                      │
└─────────────────────────────────────────────────────────┘
```

## Detalle del Cifrado

### En las nubes (Rclone Crypt)
- **Algoritmo**: AES-256 en modo CTR con HMAC-SHA256
- **Key Derivation**: scrypt con la contrasena que elegiste
- **Archivos**: Cada archivo cifrado individualmente
- **Nombres**: Cifrados con EME (para el provider parecen caracteres aleatorios)
- **Directorios**: Nombres de carpeta tambien cifrados
- **Padding**: Archivos padded para ocultar tamano original

### Que ve Mega/Google/OneDrive?
```
Tu archivo:     vacaciones_2024/playa_cancun.jpg (3.2 MB)
En la nube:     k4nf8a2m/p9x2kd8f3n1a.bin (3.2 MB + padding)
```
No pueden ver:
- Nombres de archivos
- Estructura de carpetas
- Contenido de las fotos
- Metadata (EXIF, GPS, fechas)

### En transito (red local)
- WiFi de tu casa: HTTP (confiable, red privada)
- Fuera de casa: Tailscale (WireGuard, cifrado E2E)
- Subida a nubes: HTTPS + cifrado Rclone (doble capa)

## Modelo de Amenazas

| Amenaza | Proteccion | Riesgo |
|---------|-----------|--------|
| Hackean tu cuenta de Mega | Archivos cifrados, ilegibles | BAJO |
| Roban tu notebook | Solo thumbnails locales, originales en nube | MEDIO |
| Interceptan WiFi | Red local privada, Tailscale opcional | BAJO |
| Olvidas la contrasena de cifrado | IRRECUPERABLE | CRITICO |
| Mega/Google cierran tu cuenta | Fotos distribuidas en 3 nubes | BAJO |
| Fallo de disco del notebook | Originales en la nube, se restauran | BAJO |

## Recomendaciones

### CRITICO: Respalda tu contrasena de cifrado
- **Opcion 1**: Papel en un lugar seguro (caja fuerte, sobre sellado)
- **Opcion 2**: Gestor de contrasenas (Bitwarden, 1Password)
- **Opcion 3**: Archivo cifrado en otro dispositivo (USB)
- **NUNCA**: En un post-it, en el mismo notebook, en un email

### Contrasenas recomendadas
- Base de datos Immich: Se genera automaticamente (32 chars)
- Cifrado Rclone: Minimo 16 caracteres, mezcla de tipos
- Cuenta Immich: Diferente a las demas, minimo 12 chars

### Mantenimiento de seguridad
1. Actualiza Immich mensualmente (setup actualiza automaticamente)
2. Verifica logs de sync por errores inusuales
3. Revisa accesos en Immich Admin > Users
4. Mantiene actualizado Windows (parches de seguridad)

## Limitaciones conocidas

1. **HTTP local**: El trafico iPhone->Notebook no esta cifrado en tu red WiFi
   - Mitigacion: Es tu red privada, riesgo aceptable
   - Solucion avanzada: Configurar HTTPS con certificado autofirmado

2. **Thumbnails locales**: Se quedan en el disco sin cifrar
   - Mitigacion: Son imagenes pequenas (baja resolucion)
   - Solucion avanzada: BitLocker en Windows (cifra todo el disco)

3. **Contrasena unica**: Una sola contrasena para todas las nubes
   - Mitigacion: Simplifica gestion, AES-256 es robusto
   - Solucion avanzada: Contrasenas diferentes por provider (editar rclone config)
