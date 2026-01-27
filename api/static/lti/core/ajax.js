define([], function () {
  return {
    call: function () {
      console.warn("core/ajax stub called (LTI mode)");
      return Promise.resolve([]);
    },
  };
});
