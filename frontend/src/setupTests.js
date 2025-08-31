// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfills for JSDOM under Node 21: ensure timers exist for testing-library/jest
if (typeof global.setImmediate === 'undefined') {
  global.setImmediate = (callback, ...args) => setTimeout(callback, 0, ...args);
}
if (typeof global.clearImmediate === 'undefined') {
  global.clearImmediate = (handle) => clearTimeout(handle);
}
