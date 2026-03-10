define([], function () {
  return {
    call: function (requests) {
      console.warn("[standalone] core/ajax stub – webservice call ignored");
      if (Array.isArray(requests)) {
        requests.forEach(function (req) {
          if (req.done) req.done(null);
        });
      }
      return [Promise.resolve(null)];
    },
  };
});
