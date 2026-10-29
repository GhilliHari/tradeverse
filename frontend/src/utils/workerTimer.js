/**
 * Utility to use Web Workers for intervals/timeouts to bypass background tab throttling.
 */

const workerScript = `
  const intervalIds = new Map();
  const timeoutIds = new Map();

  self.onmessage = function(e) {
    const data = e.data;
    switch(data.type) {
      case 'setInterval':
        const iId = setInterval(() => {
          self.postMessage({ id: data.id });
        }, data.ms);
        intervalIds.set(data.id, iId);
        break;
      case 'clearInterval':
        if (intervalIds.has(data.id)) {
          clearInterval(intervalIds.get(data.id));
          intervalIds.delete(data.id);
        }
        break;
      case 'setTimeout':
        const tId = setTimeout(() => {
          self.postMessage({ id: data.id });
          timeoutIds.delete(data.id);
        }, data.ms);
        timeoutIds.set(data.id, tId);
        break;
      case 'clearTimeout':
        if (timeoutIds.has(data.id)) {
          clearTimeout(timeoutIds.get(data.id));
          timeoutIds.delete(data.id);
        }
        break;
    }
  };
`;

let worker = null;
const callbacks = new Map();
let nextId = 1;

function initWorker() {
    if (!worker && typeof window !== 'undefined') {
        const blob = new Blob([workerScript], { type: 'application/javascript' });
        worker = new Worker(URL.createObjectURL(blob));
        worker.onmessage = function (e) {
            const cb = callbacks.get(e.data.id);
            if (cb) cb();
        };
    }
}

export function workerSetInterval(callback, ms) {
    initWorker();
    const id = nextId++;
    callbacks.set(id, callback);
    worker.postMessage({ type: 'setInterval', id, ms });
    return id;
}

export function workerClearInterval(id) {
    if (worker) {
        worker.postMessage({ type: 'clearInterval', id });
        callbacks.delete(id);
    }
}

export function workerSetTimeout(callback, ms) {
    initWorker();
    const id = nextId++;
    callbacks.set(id, callback);
    worker.postMessage({ type: 'setTimeout', id, ms });
    return id;
}

export function workerClearTimeout(id) {
    if (worker) {
        worker.postMessage({ type: 'clearTimeout', id });
        callbacks.delete(id);
    }
}
