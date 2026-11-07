/* Minimal QR Code encoder (byte mode, error correction level M, versions 1-40).
   Follows the structure of Project Nayuki's QR Code generator (MIT). Returns an SVG string. */
const QR = (() => {
  const ECC_PER_BLOCK_M = [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28];
  const BLOCKS_M = [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49];
  const ECL_FORMAT_BITS_M = 0;

  const bit = (x, i) => ((x >>> i) & 1) !== 0;

  function rawDataModules(ver) {
    let result = (16 * ver + 128) * ver + 64;
    if (ver >= 2) {
      const numAlign = Math.floor(ver / 7) + 2;
      result -= (25 * numAlign - 10) * numAlign - 55;
      if (ver >= 7) {
        result -= 36;
      }
    }
    return result;
  }

  function dataCodewords(ver) {
    return Math.floor(rawDataModules(ver) / 8) - ECC_PER_BLOCK_M[ver] * BLOCKS_M[ver];
  }

  function gfMul(x, y) {
    let z = 0;
    for (let i = 7; i >= 0; i--) {
      z = (z << 1) ^ ((z >>> 7) * 0x11d);
      z ^= ((y >>> i) & 1) * x;
    }
    return z & 0xff;
  }

  function rsDivisor(degree) {
    const result = new Array(degree).fill(0);
    result[degree - 1] = 1;
    let root = 1;
    for (let i = 0; i < degree; i++) {
      for (let j = 0; j < result.length; j++) {
        result[j] = gfMul(result[j], root);
        if (j + 1 < result.length) {
          result[j] ^= result[j + 1];
        }
      }
      root = gfMul(root, 0x02);
    }
    return result;
  }

  function rsRemainder(data, divisor) {
    const result = divisor.map(() => 0);
    for (const b of data) {
      const factor = b ^ result.shift();
      result.push(0);
      divisor.forEach((coef, i) => {
        result[i] ^= gfMul(coef, factor);
      });
    }
    return result;
  }

  function alignmentPositions(ver, size) {
    if (ver === 1) {
      return [];
    }
    const numAlign = Math.floor(ver / 7) + 2;
    const step = Math.floor((ver * 8 + numAlign * 3 + 5) / (numAlign * 4 - 4)) * 2;
    const result = [6];
    for (let pos = size - 7; result.length < numAlign; pos -= step) {
      result.splice(1, 0, pos);
    }
    return result;
  }

  function encode(text, forcedMask) {
    const bytes = Array.from(new TextEncoder().encode(text));
    let ver = 1;
    for (; ver <= 40; ver++) {
      const countBits = ver <= 9 ? 8 : 16;
      if (4 + countBits + bytes.length * 8 <= dataCodewords(ver) * 8) {
        break;
      }
    }
    if (ver > 40) {
      throw new Error("Text too long for a QR code");
    }
    const size = ver * 4 + 17;
    const capacityBits = dataCodewords(ver) * 8;
    const bits = [];
    const push = (value, len) => {
      for (let i = len - 1; i >= 0; i--) {
        bits.push((value >>> i) & 1);
      }
    };
    push(0x4, 4);
    push(bytes.length, ver <= 9 ? 8 : 16);
    bytes.forEach((b) => push(b, 8));
    push(0, Math.min(4, capacityBits - bits.length));
    push(0, (8 - (bits.length % 8)) % 8);
    for (let pad = 0xec; bits.length < capacityBits; pad ^= 0xec ^ 0x11) {
      push(pad, 8);
    }
    const data = [];
    for (let i = 0; i < bits.length; i += 8) {
      let byte = 0;
      for (let j = 0; j < 8; j++) {
        byte = (byte << 1) | bits[i + j];
      }
      data.push(byte);
    }

    const numBlocks = BLOCKS_M[ver];
    const blockEccLen = ECC_PER_BLOCK_M[ver];
    const rawCodewords = Math.floor(rawDataModules(ver) / 8);
    const numShortBlocks = numBlocks - (rawCodewords % numBlocks);
    const shortBlockLen = Math.floor(rawCodewords / numBlocks);
    const divisor = rsDivisor(blockEccLen);
    const blocks = [];
    for (let i = 0, k = 0; i < numBlocks; i++) {
      const dat = data.slice(k, k + shortBlockLen - blockEccLen + (i < numShortBlocks ? 0 : 1));
      k += dat.length;
      const ecc = rsRemainder(dat, divisor);
      if (i < numShortBlocks) {
        dat.push(0);
      }
      blocks.push(dat.concat(ecc));
    }
    const codewords = [];
    for (let i = 0; i < blocks[0].length; i++) {
      blocks.forEach((block, j) => {
        if (i !== shortBlockLen - blockEccLen || j >= numShortBlocks) {
          codewords.push(block[i]);
        }
      });
    }

    const modules = Array.from({ length: size }, () => new Array(size).fill(false));
    const isFunction = Array.from({ length: size }, () => new Array(size).fill(false));
    const setFunction = (x, y, dark) => {
      modules[y][x] = dark;
      isFunction[y][x] = true;
    };
    for (let i = 0; i < size; i++) {
      setFunction(6, i, i % 2 === 0);
      setFunction(i, 6, i % 2 === 0);
    }
    const finder = (cx, cy) => {
      for (let dy = -4; dy <= 4; dy++) {
        for (let dx = -4; dx <= 4; dx++) {
          const dist = Math.max(Math.abs(dx), Math.abs(dy));
          const x = cx + dx;
          const y = cy + dy;
          if (x >= 0 && x < size && y >= 0 && y < size) {
            setFunction(x, y, dist !== 2 && dist !== 4);
          }
        }
      }
    };
    finder(3, 3);
    finder(size - 4, 3);
    finder(3, size - 4);
    const align = alignmentPositions(ver, size);
    const last = align.length - 1;
    align.forEach((ax, i) => {
      align.forEach((ay, j) => {
        if ((i === 0 && j === 0) || (i === 0 && j === last) || (i === last && j === 0)) {
          return;
        }
        for (let dy = -2; dy <= 2; dy++) {
          for (let dx = -2; dx <= 2; dx++) {
            setFunction(ax + dx, ay + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
          }
        }
      });
    });
    const drawFormat = (mask) => {
      const dataBits = (ECL_FORMAT_BITS_M << 3) | mask;
      let rem = dataBits;
      for (let i = 0; i < 10; i++) {
        rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
      }
      const fmt = ((dataBits << 10) | rem) ^ 0x5412;
      for (let i = 0; i <= 5; i++) {
        setFunction(8, i, bit(fmt, i));
      }
      setFunction(8, 7, bit(fmt, 6));
      setFunction(8, 8, bit(fmt, 7));
      setFunction(7, 8, bit(fmt, 8));
      for (let i = 9; i < 15; i++) {
        setFunction(14 - i, 8, bit(fmt, i));
      }
      for (let i = 0; i < 8; i++) {
        setFunction(size - 1 - i, 8, bit(fmt, i));
      }
      for (let i = 8; i < 15; i++) {
        setFunction(8, size - 15 + i, bit(fmt, i));
      }
      setFunction(8, size - 8, true);
    };
    drawFormat(0);
    if (ver >= 7) {
      let rem = ver;
      for (let i = 0; i < 12; i++) {
        rem = (rem << 1) ^ ((rem >>> 11) * 0x1f25);
      }
      const vbits = (ver << 12) | rem;
      for (let i = 0; i < 18; i++) {
        const dark = bit(vbits, i);
        const a = size - 11 + (i % 3);
        const b = Math.floor(i / 3);
        setFunction(a, b, dark);
        setFunction(b, a, dark);
      }
    }

    let i = 0;
    for (let right = size - 1; right >= 1; right -= 2) {
      if (right === 6) {
        right = 5;
      }
      for (let vert = 0; vert < size; vert++) {
        for (let j = 0; j < 2; j++) {
          const x = right - j;
          const upward = ((right + 1) & 2) === 0;
          const y = upward ? size - 1 - vert : vert;
          if (!isFunction[y][x] && i < codewords.length * 8) {
            modules[y][x] = bit(codewords[i >>> 3], 7 - (i & 7));
            i++;
          }
        }
      }
    }

    const maskFn = [
      (x, y) => (x + y) % 2 === 0,
      (x, y) => y % 2 === 0,
      (x) => x % 3 === 0,
      (x, y) => (x + y) % 3 === 0,
      (x, y) => (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0,
      (x, y) => ((x * y) % 2) + ((x * y) % 3) === 0,
      (x, y) => (((x * y) % 2) + ((x * y) % 3)) % 2 === 0,
      (x, y) => (((x + y) % 2) + ((x * y) % 3)) % 2 === 0,
    ];
    const applyMask = (mask) => {
      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          if (!isFunction[y][x] && maskFn[mask](x, y)) {
            modules[y][x] = !modules[y][x];
          }
        }
      }
    };
    const penalty = () => {
      let score = 0;
      for (let pass = 0; pass < 2; pass++) {
        for (let a = 0; a < size; a++) {
          let run = 1;
          for (let b = 1; b < size; b++) {
            const cur = pass === 0 ? modules[a][b] : modules[b][a];
            const prev = pass === 0 ? modules[a][b - 1] : modules[b - 1][a];
            if (cur === prev) {
              run++;
              if (run === 5) {
                score += 3;
              } else if (run > 5) {
                score++;
              }
            } else {
              run = 1;
            }
          }
        }
      }
      let dark = 0;
      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          if (modules[y][x]) {
            dark++;
          }
          if (y < size - 1 && x < size - 1) {
            const c = modules[y][x];
            if (c === modules[y][x + 1] && c === modules[y + 1][x] && c === modules[y + 1][x + 1]) {
              score += 3;
            }
          }
        }
      }
      const total = size * size;
      score += Math.floor(Math.abs(dark * 20 - total * 10) / total) * 10;
      return score;
    };
    let bestMask = 0;
    let bestScore = Infinity;
    for (let mask = 0; mask < 8; mask++) {
      applyMask(mask);
      drawFormat(mask);
      const score = penalty();
      if (score < bestScore) {
        bestScore = score;
        bestMask = mask;
      }
      applyMask(mask);
    }
    if (forcedMask !== undefined) {
      bestMask = forcedMask;
    }
    applyMask(bestMask);
    drawFormat(bestMask);
    return { size, modules, version: ver };
  }

  function svg(text, label) {
    const { size, modules } = encode(text);
    const quiet = 4;
    const total = size + quiet * 2;
    let path = "";
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        if (modules[y][x]) {
          path += `M${x + quiet} ${y + quiet}h1v1h-1z`;
        }
      }
    }
    const name = String(label || "QR code").replace(/[<>&"]/g, "");
    return `<svg class="qr" viewBox="0 0 ${total} ${total}" role="img" aria-label="${name}" shape-rendering="crispEdges"><rect width="${total}" height="${total}" fill="#fff"/><path d="${path}" fill="#111"/></svg>`;
  }

  return { encode, svg };
})();
