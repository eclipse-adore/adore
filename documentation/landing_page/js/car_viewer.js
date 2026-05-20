(function () {
    const wrap = document.getElementById('car-canvas-wrap');
    const loadingEl = document.getElementById('car-loading');
    if (!wrap) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(wrap.clientWidth, wrap.clientHeight);
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setClearColor(0x0f1318, 1);
    wrap.appendChild(renderer.domElement);

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(38, wrap.clientWidth / wrap.clientHeight, 0.1, 200);
    camera.position.set(-4.5, 2.4, 4.2);
    camera.lookAt(0, 0.6, 0);

    // ── Sky gradient background ───────────────────────────────────────
    // Rendered as a fullscreen quad behind everything
    const skyScene  = new THREE.Scene();
    const skyCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const skyGeo = new THREE.PlaneGeometry(2, 2);
    const skyMat = new THREE.ShaderMaterial({
        depthWrite: false,
        uniforms: {
            uTop:    { value: new THREE.Color(0x1a6fc4) },
            uBottom: { value: new THREE.Color(0x7ec8e3) },
        },
        vertexShader: `
            varying vec2 vUv;
            void main() { vUv = uv; gl_Position = vec4(position, 1.0); }
        `,
        fragmentShader: `
            uniform vec3 uTop;
            uniform vec3 uBottom;
            varying vec2 vUv;
            void main() { gl_FragColor = vec4(mix(uBottom, uTop, vUv.y), 1.0); }
        `,
    });
    skyScene.add(new THREE.Mesh(skyGeo, skyMat));

    // ── Sun (billboard sprite) ────────────────────────────────────────
    const sunCanvas = document.createElement('canvas');
    sunCanvas.width = sunCanvas.height = 128;
    const sc = sunCanvas.getContext('2d');

    // Outer glow
    const glow = sc.createRadialGradient(64, 64, 18, 64, 64, 64);
    glow.addColorStop(0,   'rgba(255,240,100,0.55)');
    glow.addColorStop(0.5, 'rgba(255,210,60,0.15)');
    glow.addColorStop(1,   'rgba(255,200,0,0)');
    sc.fillStyle = glow;
    sc.fillRect(0, 0, 128, 128);

    // Sun disc
    const disc = sc.createRadialGradient(64, 64, 0, 64, 64, 22);
    disc.addColorStop(0,   '#fff9c4');
    disc.addColorStop(0.6, '#ffe033');
    disc.addColorStop(1,   '#ffb300');
    sc.beginPath();
    sc.arc(64, 64, 22, 0, Math.PI * 2);
    sc.fillStyle = disc;
    sc.fill();

    // Cartoon rays
    sc.strokeStyle = '#ffe066';
    sc.lineWidth = 2.5;
    sc.lineCap = 'round';
    for (let i = 0; i < 12; i++) {
        const angle = (i / 12) * Math.PI * 2;
        const r0 = 26, r1 = 36 + (i % 3 === 0 ? 8 : 0);
        sc.beginPath();
        sc.moveTo(64 + Math.cos(angle) * r0, 64 + Math.sin(angle) * r0);
        sc.lineTo(64 + Math.cos(angle) * r1, 64 + Math.sin(angle) * r1);
        sc.stroke();
    }

    const sunTex = new THREE.CanvasTexture(sunCanvas);
    const sunSprite = new THREE.Sprite(new THREE.SpriteMaterial({
        map: sunTex, transparent: true, depthWrite: false, depthTest: false
    }));
    sunSprite.scale.set(4.5, 4.5, 1);
    sunSprite.position.set(18, 14, -60);
    scene.add(sunSprite);

    // ── Lighting ──────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xcce8ff, 0.7));

    const sun = new THREE.DirectionalLight(0xfff5d0, 1.4);
    sun.position.set(5, 12, 6);
    sun.castShadow = true;
    sun.shadow.mapSize.set(1024, 1024);
    sun.shadow.camera.near = 1;
    sun.shadow.camera.far  = 30;
    sun.shadow.camera.left = sun.shadow.camera.bottom = -6;
    sun.shadow.camera.right = sun.shadow.camera.top   =  6;
    sun.shadow.bias = -0.001;
    scene.add(sun);

    const fill = new THREE.DirectionalLight(0x4DB6AC, 0.18);
    fill.position.set(-4, 2, -3);
    scene.add(fill);

    // ── Road ─────────────────────────────────────────────────────────
    const ROAD_W       = 8;
    const ROAD_L       = 40;
    const LANE_W       = ROAD_W / 2;
    const DASH_SPACING = 2.4;
    const DASH_LEN     = 1.2;
    const NUM_DASHES   = Math.ceil(ROAD_L / DASH_SPACING) + 2;

    const tarmac = new THREE.Mesh(
        new THREE.PlaneGeometry(ROAD_W, ROAD_L),
        new THREE.MeshStandardMaterial({ color: 0x252830, roughness: 0.94 })
    );
    tarmac.rotation.x = -Math.PI / 2;
    tarmac.receiveShadow = true;
    scene.add(tarmac);

    [-1, 1].forEach(side => {
        const sh = new THREE.Mesh(
            new THREE.PlaneGeometry(3.5, ROAD_L),
            new THREE.MeshStandardMaterial({ color: 0x353840, roughness: 0.97 })
        );
        sh.rotation.x = -Math.PI / 2;
        sh.position.x = side * (ROAD_W / 2 + 1.75);
        sh.receiveShadow = true;
        scene.add(sh);
    });

    const edgeMat = new THREE.MeshStandardMaterial({ color: 0xe0ddd0, roughness: 0.55 });
    [-1, 1].forEach(side => {
        const edge = new THREE.Mesh(new THREE.PlaneGeometry(0.12, ROAD_L), edgeMat);
        edge.rotation.x = -Math.PI / 2;
        edge.position.set(side * (ROAD_W / 2 - 0.08), 0.003, 0);
        scene.add(edge);
    });

    // Animated dash group
    const dashGroup = new THREE.Group();
    scene.add(dashGroup);
    const dashGeo = new THREE.PlaneGeometry(0.11, DASH_LEN);
    dashGeo.rotateX(-Math.PI / 2);
    const dashMatYellow = new THREE.MeshStandardMaterial({ color: 0xd4b400, roughness: 0.5, metalness: 0.08 });

    for (let i = 0; i < NUM_DASHES; i++) {
        const m = new THREE.Mesh(dashGeo, dashMatYellow);
        m.position.set(0, 0.003, (i - NUM_DASHES / 2) * DASH_SPACING);
        dashGroup.add(m);
    }

    // ── Materials ─────────────────────────────────────────────────────
    const matBlack  = new THREE.MeshStandardMaterial({ color: 0x141618, metalness: 0.5,  roughness: 0.5  });
    const matWhite  = new THREE.MeshStandardMaterial({ color: 0xddeae8, metalness: 0.2,  roughness: 0.28 });
    const matGreen  = new THREE.MeshStandardMaterial({ color: 0x4caf50, metalness: 0.05, roughness: 0.5  });
    const matWindow = new THREE.MeshStandardMaterial({ color: 0x1b3848, metalness: 0.15, roughness: 0.08, transparent: true, opacity: 0.80, depthWrite: false });
    const matSticker= new THREE.MeshStandardMaterial({ color: 0xf2f0ee, metalness: 0.0,  roughness: 0.6  });

    const matMap = {
        'BLACK-material':         matBlack,
        'WHITE-material':         matWhite,
        'Green-material':         matGreen,
        'Window-material':        matWindow,
        'sticker_white-material': matSticker,
    };

    function pickMat(m) {
        if (!m) return matBlack;
        if (matMap[m.name]) return matMap[m.name];
        const n = m.name.toLowerCase();
        if (n.includes('window'))  return matWindow;
        if (n.includes('green'))   return matGreen;
        if (n.includes('sticker')) return matSticker;
        if (n.includes('white'))   return matWhite;
        return matBlack;
    }

    // ── Load model ────────────────────────────────────────────────────
    let carGroup = null;
    let userYaw  = 0;

    const loader = new THREE.ColladaLoader();
    loader.load('img/car_model.dae', function (collada) {
        carGroup = new THREE.Group();
        const model = collada.scene;

        const box    = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size   = box.getSize(new THREE.Vector3());
        const scale  = 2.4 / Math.max(size.x, size.y, size.z);

        model.position.sub(center);
        model.scale.setScalar(scale);

        model.traverse(function (child) {
            if (!child.isMesh) return;
            child.castShadow    = true;
            child.receiveShadow = false;
            const mats = Array.isArray(child.material) ? child.material : [child.material];
            child.material = mats.length === 1 ? pickMat(mats[0]) : mats.map(pickMat);
        });

        carGroup.add(model);
        scene.add(carGroup);

        // Sit on road
        const b2 = new THREE.Box3().setFromObject(carGroup);
        carGroup.position.y = -b2.min.y;

        // Right lane
        carGroup.position.x = LANE_W / 2;

        // Face forward (PI) then -90 deg
        carGroup.rotation.y = Math.PI / 2;



        if (loadingEl) loadingEl.style.display = 'none';

    }, undefined, function (err) {
        if (loadingEl) loadingEl.textContent = 'Model unavailable';
        console.warn('ColladaLoader:', err);
    });

    // ── Drag to orbit camera ──────────────────────────────────────────
    const BASE_ANGLE = Math.PI * 0.7;
    const CAM_R = 6.5, CAM_H = 2.4;

    function updateCamera() {
        const cx = carGroup ? carGroup.position.x : LANE_W / 2;
        camera.position.set(
            Math.sin(BASE_ANGLE + userYaw) * CAM_R + cx,
            CAM_H,
            Math.cos(BASE_ANGLE + userYaw) * CAM_R
        );
        camera.lookAt(cx, 0.6, 0);
    }

    let dragging = false, px = 0;
    wrap.addEventListener('mousedown', e => { dragging = true; px = e.clientX; });
    window.addEventListener('mousemove', e => {
        if (!dragging) return;
        userYaw += (e.clientX - px) * 0.011;
        px = e.clientX;
        updateCamera();
    });
    window.addEventListener('mouseup', () => { dragging = false; });

    wrap.addEventListener('touchstart', e => { px = e.touches[0].clientX; }, { passive: true });
    wrap.addEventListener('touchmove', e => {
        userYaw += (e.touches[0].clientX - px) * 0.013;
        px = e.touches[0].clientX;
        updateCamera();
    }, { passive: true });

    window.addEventListener('resize', () => {
        const w = wrap.clientWidth, h = wrap.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    });

    // ── Render loop ───────────────────────────────────────────────────
    const ROAD_SPEED = 0.035;
    let dashOffset = 0;

    renderer.autoClear = false;
    (function animate() {
        requestAnimationFrame(animate);

        dashOffset = (dashOffset + ROAD_SPEED) % DASH_SPACING;
        dashGroup.position.z = dashOffset;

        renderer.clear();
        renderer.render(skyScene, skyCamera);
        renderer.clearDepth();
        renderer.render(scene, camera);
    })();
})();
