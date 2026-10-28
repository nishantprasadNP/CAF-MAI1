// Prepares a CSV for upload in the browser.
//
// Large files are randomly sampled down to `maxRows` data rows (reservoir
// sampling, one pass, no need to know the row count up front) and gzip-
// compressed. A 471 MB / 6.3M-row CSV becomes ~29 MB, so the upload takes
// seconds instead of minutes and the server never holds the whole file.

const SMALL_FILE_BYTES = 5 * 1024 * 1024;

function supportsGzip() {
  return typeof CompressionStream !== "undefined";
}

async function gzipBlob(blob) {
  const stream = blob.stream().pipeThrough(new CompressionStream("gzip"));
  return new Response(stream).blob();
}

function countQuotes(line) {
  let n = 0;
  for (let i = line.indexOf('"'); i !== -1; i = line.indexOf('"', i + 1)) n++;
  return n;
}

// Reads the file line by line. Returns null if a quoted field spans lines,
// because line-based sampling would then corrupt rows.
async function sampleLines(file, maxRows, onProgress) {
  const reader = file.stream().pipeThrough(new TextDecoderStream()).getReader();
  let carry = "";
  let header = null;
  let seen = 0;
  let bytesRead = 0;
  const reservoir = [];

  const take = (raw) => {
    const line = raw.endsWith("\r") ? raw.slice(0, -1) : raw;
    if (header === null) {
      header = line;
      return true;
    }
    if (line === "") return true;
    if (line.includes('"') && countQuotes(line) % 2 === 1) return false;
    if (seen < maxRows) {
      reservoir.push(line);
    } else {
      const j = Math.floor(Math.random() * (seen + 1));
      if (j < maxRows) reservoir[j] = line;
    }
    seen++;
    return true;
  };

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    bytesRead += value.length; // characters ≈ bytes for typical CSVs
    const parts = (carry + value).split("\n");
    carry = parts.pop();
    for (const part of parts) {
      if (!take(part)) {
        await reader.cancel();
        return null;
      }
    }
    onProgress?.(Math.min(99, Math.round((bytesRead / file.size) * 100)));
  }
  if (carry && !take(carry)) return null;

  return { header, rows: reservoir, totalRows: seen };
}

/**
 * @returns {Promise<{blob: Blob, filename: string, sampled: boolean,
 *   totalRows: number | null, keptRows: number | null}>}
 */
export async function prepareUpload(file, { maxRows, onPhase }) {
  if (file.size <= SMALL_FILE_BYTES) {
    return { blob: file, filename: file.name, sampled: false, totalRows: null, keptRows: null };
  }

  onPhase?.("Reading file… 0%");
  const sample = await sampleLines(file, maxRows, (pct) => onPhase?.(`Reading file… ${pct}%`));

  if (sample === null || sample.totalRows <= maxRows) {
    // Keep every row; just compress (or send as-is if the browser can't).
    if (!supportsGzip()) {
      return { blob: file, filename: file.name, sampled: false, totalRows: sample?.totalRows ?? null, keptRows: null };
    }
    onPhase?.("Compressing…");
    return {
      blob: await gzipBlob(file),
      filename: `${file.name}.gz`,
      sampled: false,
      totalRows: sample?.totalRows ?? null,
      keptRows: sample?.totalRows ?? null,
    };
  }

  onPhase?.("Compressing sample…");
  const csv = new Blob([sample.header, "\n", sample.rows.join("\n"), "\n"], { type: "text/csv" });
  const gz = supportsGzip();
  return {
    blob: gz ? await gzipBlob(csv) : csv,
    filename: gz ? `${file.name}.sample.csv.gz` : `${file.name}.sample.csv`,
    sampled: true,
    totalRows: sample.totalRows,
    keptRows: sample.rows.length,
  };
}
